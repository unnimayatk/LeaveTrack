from django import forms
from .models import LeaveRequest, InServiceCourse, LeaveApplication
from django.contrib.auth.models import User
from django import forms
from .models import InServiceCourse
from datetime import date
from django.core.exceptions import ValidationError

# Leave Request Form

class LeaveRequestForm(forms.ModelForm):
    suffixed_leave = forms.BooleanField(required=False, label="Suffixed Leave")
    prefixed_leave = forms.BooleanField(required=False, label="Prefixed Leave")
    medical_certificate = forms.FileField(required=False, label="Upload Medical Certificate")

    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason', 'suffixed_leave', 'prefixed_leave', 'medical_certificate']
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

        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError("❌ End Date cannot be before Start Date!")
        
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

        today = date.today()

        if start_date and start_date < today:
            self.add_error('start_date', "⚠️ Start date cannot be in the past!")

        if end_date and end_date < today:
            self.add_error('end_date', "⚠️ End date cannot be in the past!")

        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', "⚠️ End date must be after the start date!")

        return cleaned_data


# Leave Application Form
class ApplyLeaveForm(forms.ModelForm):
    class Meta:
        model = LeaveApplication
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
        if not self.user:
            raise ValueError("User must be provided")

    def clean(self):
        cleaned_data = super().clean()
        leave_type = cleaned_data.get('leave_type')
        prefixed_leave = cleaned_data.get('prefixed_leave')
        suffixed_leave = cleaned_data.get('suffixed_leave')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if leave_type not in LeaveApplication.ELIGIBLE_FOR_SUFFIX_PREFIX:
            if prefixed_leave or suffixed_leave:
                raise forms.ValidationError("❌ Prefixed/Suffixed leave only allowed for Earned or Half Pay leaves.")

        if self.user and start_date and end_date:
            overlapping = LeaveApplication.objects.filter(
                user=self.user,
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            if overlapping.exists():
                raise forms.ValidationError("❌ You already have a leave request during these dates.")

        return cleaned_data
