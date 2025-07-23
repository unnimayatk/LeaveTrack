from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone

# ---------------- Notification ----------------

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user}" 


# ---------------- Leave Balance ----------------

def get_current_year():
    return datetime.now().year

class LeaveBalance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    current_year = models.PositiveIntegerField(default=get_current_year)

    casual_leave = models.PositiveIntegerField(default=25)
    earned_leave = models.PositiveIntegerField(default=33)
    half_pay_leave = models.PositiveIntegerField(default=20)
    maternity_leave = models.PositiveIntegerField(default=180)
    paternity_leave = models.PositiveIntegerField(default=10)

    def __str__(self):
        return f"{self.user.username} - {self.current_year}"


# ---------------- Leave Request ----------------
class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('casual', 'Casual Leave'),
        ('earned', 'Earned Leave'),
        ('half_pay', 'Half Pay Leave'),
        ('commuted', 'Commuted Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('special', 'Special Leave'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    applied_on = models.DateTimeField(auto_now_add=True)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True, null=True)
    
    # New fields for prefix and suffix
    prefixed_leave = models.BooleanField(default=False)
    suffixed_leave = models.BooleanField(default=False)

    prefixed_count   = models.PositiveIntegerField(default=0)
    suffixed_count   = models.PositiveIntegerField(default=0)
    
    medical_certificate = models.FileField(
        upload_to='certificates/',
        blank=True,
        null=True
    )
    deduction_done = models.BooleanField(default=False)

    def get_leave_days(self):
        """Calculate the total number of leave days, including both start and end dates."""
        return (self.end_date - self.start_date).days + 1

    def deduct_leave_balance(self):
        """Deduct the leave days from the user's balance based on the leave type."""
        year = self.start_date.year
        leave_days = self.get_leave_days()

        # Get or create the user's leave balance for the current year
        leave_balance, created = LeaveBalance.objects.get_or_create(user=self.user, current_year=year)

        print(f"[Deducting] {self.leave_type} leave for {self.user.username} - {leave_days} day(s)")

        # Deduct leave based on the leave type
        if self.leave_type == 'casual':
            leave_balance.casual_leave -= leave_days

        elif self.leave_type == 'earned':
            leave_balance.earned_leave -= leave_days

        elif self.leave_type == 'half_pay':
            leave_balance.half_pay_leave -= leave_days

        elif self.leave_type == 'commuted':
            leave_balance.half_pay_leave -= (leave_days * 2)  # Assuming commuted leave counts as double days

        elif self.leave_type == 'maternity':
            leave_balance.maternity_leave -= leave_days

        elif self.leave_type == 'paternity':
            leave_balance.paternity_leave -= leave_days

        # Prevent going below zero leave balance
        leave_balance.casual_leave = max(leave_balance.casual_leave, 0)
        leave_balance.earned_leave = max(leave_balance.earned_leave, 0)
        leave_balance.half_pay_leave = max(leave_balance.half_pay_leave, 0)
        leave_balance.maternity_leave = max(leave_balance.maternity_leave, 0)
        leave_balance.paternity_leave = max(leave_balance.paternity_leave, 0)

        leave_balance.save()

    def save(self, *args, **kwargs):
        print(f"Saving leave with status: {self.status} for {self.user.username}")
        
        if self.status == 'approved' and not self.deduction_done:
            print(f"[Deduction triggered] for {self.user.username}")
            self.deduct_leave_balance()
            self.deduction_done = True
        
        # Handle prefix/suffix logic here
        if self.prefixed_leave:
            print("Applying prefix leave days")
            # Add logic to adjust the leave days based on holidays before the leave start date
            # Example: self.prefixed_count = 1 for one holiday before the leave

        if self.suffixed_leave:
            print("Applying suffix leave days")
            # Add logic to adjust the leave days based on holidays after the leave end date
            # Example: self.suffixed_count = 1 for one holiday after the leave
    
        if self.status == 'approved':
            self.rejection_reason = ''

        super().save(*args, **kwargs)

    @staticmethod
    def current_year():
        return datetime.now().year 


# ---------------- In-Service Course ----------------

class InServiceCourse(models.Model):
    COURSE_TYPES = [
        ('kerala', 'Inside Kerala'),
        ('national', 'National Level'),
        ('international', 'International Level'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_type = models.CharField(max_length=20, choices=COURSE_TYPES)
    course_name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    certificate = models.FileField(upload_to='course_certificates/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course_name} ({self.user.username})"

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("End date cannot be before start date.")

        if self.end_date:
            today = timezone.now().date()
            upload_start = self.end_date
            upload_deadline = self.end_date + timedelta(days=14)

            if today < upload_start:
                raise ValidationError(
                    f"⚠️ Certificate can only be uploaded after the course ends on {upload_start.strftime('%B %d, %Y')}."
                )
            if today > upload_deadline:
                raise ValidationError(
                    f"⚠️ Certificate must be uploaded within 14 days of course completion. Deadline was {upload_deadline.strftime('%B %d, %Y')}."
                )
            if not self.certificate:
                raise ValidationError("⚠️ Certificate is required and must be uploaded during the allowed window.")

        return super().clean()


# ---------------- Holidays ----------------

class Holiday(models.Model):
    date = models.DateField(unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.date})"
