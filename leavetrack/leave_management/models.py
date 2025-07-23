from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError


from django.db import models
from django.contrib.auth.models import User

class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('casual', 'Casual Leave'),
        ('earned', 'Earned Leave'),
        ('half_pay', 'Half Pay Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('with_allowance', 'Leave with Allowance'),
        ('without_allowance', 'Leave without Allowance'),
        ('special', 'Special Leave'),
    ]

    ELIGIBLE_FOR_SUFFIX_PREFIX = ['earned', 'half_pay']  # Only these leave types allow suffix/prefix

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Links to the User model
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)  # Leave type choices
    start_date = models.DateField()  # Start date for leave
    end_date = models.DateField()  # End date for leave
    reason = models.TextField()  # Reason for applying leave
    suffixed_leave = models.BooleanField(default=False)  # Flag for suffixed leave
    prefixed_leave = models.BooleanField(default=False)  # Flag for prefixed leave
    medical_certificate = models.FileField(upload_to='certificates/', null=True, blank=True)  # Medical certificate upload
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # Status of the leave
    applied_on = models.DateTimeField(auto_now_add=True)  # Timestamp of when the leave was applied

    def save(self, *args, **kwargs):
        """ Restrict Suffixed & Prefixed Leave to specific leave types """
        if self.leave_type not in self.ELIGIBLE_FOR_SUFFIX_PREFIX:
            self.suffixed_leave = False
            self.prefixed_leave = False
        
        super().save(*args, **kwargs)  # Call the default save method

    def __str__(self):
        return f"{self.user.username} - {self.leave_type} ({self.status})"




class LeaveBalance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    year = models.PositiveIntegerField(default=datetime.now().year)  # 👈 Add this line

    casual_leave = models.IntegerField(default=25)
    earned_leave = models.IntegerField(default=33)
    half_pay_leave = models.IntegerField(default=20)
    maternity_leave = models.IntegerField(default=180)
    paternity_leave = models.IntegerField(default=10)

    def __str__(self):
        return f"{self.user.username} - {self.year}"

class InServiceCourse(models.Model):
    COURSE_TYPE_CHOICES = [
        ('Inside Kerala', 'Inside Kerala'),
        ('National Level', 'National Level'),
        ('International Level', 'International Level'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_type = models.CharField(max_length=50, choices=COURSE_TYPE_CHOICES)
    course_name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    certificate = models.FileField(upload_to='certificates/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.course_name

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("End date must be after start date.")

        if self.certificate:
            deadline = self.end_date + timedelta(days=7)
            today = timezone.now().date()
            if today > deadline:
            # Optional: Set late flag instead of raising error
                self.certificate_late = True  # if such a field exists
            # Or show warning via messages in the form view

        return super().clean()

    def certificate_upload_deadline(self):
        """Calculates the deadline for uploading the certificate (7 days after the end date)."""
        return self.end_date + timedelta(days=7)



class LeaveApplication(models.Model):
    LEAVE_TYPES = [
        ('Casual Leave', 'Casual Leave'),
        ('Earned Leave', 'Earned Leave'),
        ('Half Pay Leave', 'Half Pay Leave'),
        ('Maternity Leave', 'Maternity Leave'),
        ('Paternity Leave', 'Paternity Leave'),
        ('Special Leave', 'Special Leave'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()

    # 🔥 Add these
    prefixed_leave = models.BooleanField(default=False)
    suffixed_leave = models.BooleanField(default=False)
    medical_certificate = models.FileField(upload_to='medical_certificates/', blank=True, null=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    applied_on = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        leave_balance, created = LeaveBalance.objects.get_or_create(user=self.user)  
        if self.status == "Approved":
            if self.leave_type == "Casual Leave":
                leave_balance.casual_leave -= 1
            elif self.leave_type == "Earned Leave":
                leave_balance.earned_leave -= 1
            elif self.leave_type == "Half Pay Leave":
                leave_balance.half_pay_leave -= 1
                leave_balance.commuted_leave = leave_balance.calculate_commuted_leave()
        leave_balance.save()
        super().save(*args, **kwargs)

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
