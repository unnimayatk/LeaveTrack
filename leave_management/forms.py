from django import forms
from .models import LeaveRequest, InServiceCourse
from django.contrib.auth.models import User
from datetime import date, timedelta
from django.core.exceptions import ValidationError

# Leave Request Form
class LeaveRequestForm(forms.ModelForm):
    prefixed_leave = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Prefixed Leave"
    )
    suffixed_leave = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Suffixed Leave"
    )
    medical_certificate = forms.FileField(
        required=False, 
        label="Upload Medical Certificate"
    )

    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason', 'prefixed_leave', 'suffixed_leave', 'medical_certificate']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'leave_type': forms.Select(attrs={'class': 'form-control', 'id': 'leave_type'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        prefixed_leave = cleaned_data.get("prefixed_leave")
        suffixed_leave = cleaned_data.get("suffixed_leave")

        # Validate date order
        if start_date and end_date and end_date < start_date:
            raise ValidationError("❌ End Date cannot be before Start Date!")

        # Prevent both prefixed and suffixed leave
        if prefixed_leave and suffixed_leave:
            raise ValidationError("❌ You cannot select both Prefixed and Suffixed leave at the same time.")

        return cleaned_data


# Registration Form
class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        email = cleaned_data.get("email")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match!")

        # Check if email already exists
        if email and User.objects.filter(email=email).exists():
            self.add_error('email', "An account with this email already exists.")

        return cleaned_data


# In-Service Course Form
class InServiceCourseForm(forms.ModelForm):
    class Meta:
        model = InServiceCourse
        fields = ['course_type', 'course_name', 'start_date', 'end_date', 'certificate']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'course_name': forms.TextInput(attrs={'class': 'form-control'}),
            'course_type': forms.Select(attrs={'class': 'form-control'}),
            'certificate': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        certificate = cleaned_data.get('certificate')
        today = date.today()

        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', "End date cannot be before start date.")

        if not certificate:
            self.add_error('certificate', "⚠️ Certificate is required.")

        if certificate and end_date:
            upload_start = end_date
            upload_deadline = end_date + timedelta(days=14)

            if today < upload_start:
                self.add_error(
                    'certificate',
                    f"⚠️ Certificate can only be uploaded after the course ends on {upload_start.strftime('%B %d, %Y')}."
                )
            elif today > upload_deadline:
                self.add_error(
                    'certificate',
                    f"⚠️ Certificate must be uploaded within 14 days of course completion. Deadline was {upload_deadline.strftime('%B %d, %Y')}."
                )

        return cleaned_data


# Leave Application Form (for end users)
class ApplyLeaveForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest  # ✅ Corrected from LeaveRequestForm
        fields = ['leave_type', 'start_date', 'end_date', 'prefixed_leave', 'suffixed_leave', 'reason', 'medical_certificate']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'leave_type': forms.Select(attrs={'class': 'form-select', 'id': 'leave_type'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'prefixed_leave': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'suffixed_leave': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'medical_certificate': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if self.user and start_date and end_date:
            overlapping_leaves = LeaveRequest.objects.filter(
                user=self.user,
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            if overlapping_leaves.exists():
                raise forms.ValidationError("❌ You already have a leave request during these dates.")

        return cleaned_data
