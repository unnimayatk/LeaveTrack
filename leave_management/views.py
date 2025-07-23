from datetime import datetime, timedelta
from leave_management.utils.leave_utils import get_prefixed_holidays, get_suffixed_holidays
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from .forms import ApplyLeaveForm, InServiceCourseForm, LeaveRequestForm, RegisterForm
from .models import LeaveBalance, LeaveRequest, InServiceCourse, Notification



#function to check if user is admin 
def is_admin(user):
    return user.is_superuser

# Home Page
def home(request):
    if request.user.is_authenticated:
        return redirect('leave_status')  # Change 'leave_status' to your dashboard or main logged-in page
    return render(request, 'leave_management/home.html')

def dashboard_redirect_view(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    else:
        return redirect('user_dashboard')


# Registration View
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            messages.success(request, "✅ Registration successful! You can now log in.")
            return redirect("login")
        else:
            messages.error(request, "❌ Registration failed! Please correct the errors.")
    else:
        form = RegisterForm()
    
    return render(request, "leave_management/register.html", {"form": form})


# Login View
def login_view(request):
    storage = messages.get_messages(request)
    storage.used = True  
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, '✅ Login Successful')
            return redirect('dashboard')
        else:
            messages.error(request, '❌ Invalid username or password')  # Make sure this line is here

    return render(request, 'leave_management/login.html')



# Logout View
def logout_view(request):
    messages.success(request, "✅ Logout Successful!")
    logout(request)
    return redirect('login')


# Apply for Leave
@login_required
def apply_leave(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, request.FILES)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            leave_type = form.cleaned_data['leave_type']

            # Check if a similar leave already exists
            existing = LeaveRequest.objects.filter(
                user=request.user,
                start_date=start_date,
                end_date=end_date,
                leave_type=leave_type,
                status='pending'
            ).exists()

            if existing:
                messages.warning(request, "You have already applied for this leave.")
                return redirect('dashboard')

            # Create but don't save yet
            leave_request = form.save(commit=False)
            leave_request.user = request.user  # 👈 FIXED LINE
            try:
                leave_request.clean()
            except ValidationError as e:
                messages.error(request, e.message)
                return render(request, "leave_management/apply_leave.html", {'form': form})

            leave_request.save()

            # Notify admin
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                Notification.objects.create(
                    user=admin_user,
                    message=f"{request.user.username} applied for {leave_request.leave_type} leave from {leave_request.start_date} to {leave_request.end_date}.",
                )

            messages.success(request, "Your leave request has been submitted successfully.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = LeaveRequestForm()

    return render(request, "leave_management/apply_leave.html", {'form': form})


# My Leaves Page
@login_required
def my_leaves(request):
    leave_requests = LeaveRequest.objects.filter(user=request.user).order_by('-start_date')
    current_year = now().year 
    leave_balance , created = LeaveBalance.objects.get_or_create(user=request.user, current_year=current_year)
    return render(request, 'leave_management/my_leaves.html', {
        'leave_requests': leave_requests,
        'leave_balance': leave_balance,
        'year': current_year
    })

# Dashboard View
@login_required
def dashboard(request):
    uploaded_courses = InServiceCourse.objects.filter(user=request.user).order_by('-start_date')
    return render(request, 'leave_management/dashboard.html', {
        'uploaded_courses': uploaded_courses
    })


# Leave Status Page
@login_required
def leave_status(request):
    year = datetime.now().year
    leave_requests = LeaveRequest.objects.filter(user=request.user).order_by('-applied_on')
    
    try:
        leave_balance = LeaveBalance.objects.get(user=request.user, current_year=year)
    except LeaveBalance.DoesNotExist:
        leave_balance = None

    context = {
        'leave_requests': leave_requests,
        'leave_balance': leave_balance,
        'year': year,
    }
    return render(request, 'leave_management/leave_status.html', context)


# In-Service Course Upload
@login_required
def inservice_course(request):
    if request.method == 'POST':
        form = InServiceCourseForm(request.POST, request.FILES)
        if form.is_valid():
            form.instance.user = request.user  # if needed
            form.save()
            messages.success(request, 'Course submitted successfully.')
            return redirect('inservice_course')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = InServiceCourseForm()

    courses = InServiceCourse.objects.filter(user=request.user).order_by('-start_date')
    return render(request, 'leave_management/inservice_course.html', {
        'form': form,
        'courses': courses
    })

# Admin Dashboard View
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_users = User.objects.count()
    total_leave_requests = LeaveRequest.objects.count()
    pending_leaves = LeaveRequest.objects.filter(status="Pending").count()
    approved_leaves = LeaveRequest.objects.filter(status="Approved").count()
    rejected_leaves = LeaveRequest.objects.filter(status="Rejected").count()

    notif_count = Notification.objects.filter(user=request.user, is_read=False).count()

    context = {
        "total_users": total_users,
        "total_leave_requests": total_leave_requests,
        "pending_leaves": pending_leaves,
        "approved_leaves": approved_leaves,
        "rejected_leaves": rejected_leaves,
        "unseen_notifications": notif_count,  
    }
    return render(request, "leave_management/admin_dashboard.html", context)


#Admin In-Service Course Management
@staff_member_required
def admin_certificates_view(request):
    certificates = InServiceCourse.objects.all()
    return render(request, 'leave_management/admin_certificates.html', {'certificates': certificates})

@staff_member_required
def edit_certificate(request, pk):
    cert = get_object_or_404(InServiceCourse, pk=pk)
    form = InServiceCourseForm(request.POST or None, request.FILES or None, instance=cert)
    if form.is_valid():
        form.save()
        return redirect('admin_certificates')
    return render(request, 'leave_management/edit_certificate.html', {'form': form, 'cert': cert})

@staff_member_required
def delete_certificate(request, pk):
    cert = get_object_or_404(InServiceCourse, pk=pk)
    cert.delete()
    return redirect('admin_certificates')

# Admin Leave Requests View
@login_required
@user_passes_test(is_admin)
@staff_member_required
def admin_leave_requests(request):
    leave_requests = LeaveRequest.objects.all().order_by('-applied_on')
    return render(request, 'leave_management/admin_leave_requests.html', {
        'leave_requests': leave_requests
    })


# Approve Leave Request
@login_required
@user_passes_test(is_admin)
def approve_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    if leave.status != 'approved':
        # 1) Approve and save
        leave.status = 'approved'
        leave.save()

        # 2) Deduct from LeaveBalance
        leave_days = (leave.end_date - leave.start_date).days + 1
        current_year = leave.start_date.year
        lb = LeaveBalance.objects.filter(user=leave.user, year=current_year).first()
        if lb:
            if leave.leave_type == 'casual':
                lb.casual_leave = max(lb.casual_leave - leave_days, 0)
            elif leave.leave_type == 'earned':
                lb.earned_leave = max(lb.earned_leave - leave_days, 0)
            elif leave.leave_type == 'half_pay':
                lb.half_pay_leave = max(lb.half_pay_leave - leave_days, 0)
            elif leave.leave_type == 'maternity':
                lb.maternity_leave = max(lb.maternity_leave - leave_days, 0)
            elif leave.leave_type == 'paternity':
                lb.paternity_leave = max(lb.paternity_leave - leave_days, 0)
            lb.save()

        # 3) Notify the user
        Notification.objects.create(
            user=leave.user,
            message=(
                f"✅ Your {leave.leave_type} leave from "
                f"{leave.start_date} to {leave.end_date} has been approved."
            )
        )

        messages.success(request, f"{leave.user.username}'s leave approved.")
    return redirect('admin_leave_requests')

# Reject Leave
@login_required
@user_passes_test(is_admin)
def reject_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    if leave.status != 'rejected':
        leave.status = 'rejected'
        leave.rejection_reason = request.POST.get('rejection_reason', 'No reason provided')
        leave.save()

        # Notify the user
        Notification.objects.create(
            user=leave.user,
            message=(
                f"❌ Your {leave.leave_type} leave from "
                f"{leave.start_date} to {leave.end_date} was rejected. "
                f"Reason: {leave.rejection_reason}"
            )
        )

        messages.error(request, f"{leave.user.username}'s leave rejected.")
    return redirect('admin_leave_requests')


# Approve/Reject Leave (POST Based)
@login_required
@user_passes_test(is_admin)
def approve_reject_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            leave.status = 'approved'
            messages.success(request, "✅ Leave Approved Successfully!")

        elif action == 'reject':
            leave.status = 'rejected'
            # grab the rejection reason from the form (if you have one)
            reject_reason = request.POST.get('rejection_reason', 'No reason provided')
            leave.rejection_reason = reject_reason
            messages.error(request, "❌ Leave Rejected Successfully!")

        else:
            messages.error(request, "❌ Invalid action.")
            return redirect('admin_leave_requests')

        # Persist status & any rejection reason
        leave.save()

        # Create a notification for the user who applied
        if leave.status == 'approved':
            Notification.objects.create(
                user=leave.user,
                message=(
                    f"✅ Your {leave.leave_type} leave from "
                    f"{leave.start_date} to {leave.end_date} has been approved."
                )
            )
        else:  # rejected
            Notification.objects.create(
                user=leave.user,
                message=(
                    f"❌ Your {leave.leave_type} leave from "
                    f"{leave.start_date} to {leave.end_date} was rejected. "
                    f"Reason: {leave.rejection_reason}"
                )
            )

    return redirect('admin_leave_requests')



#update leave status (for admin)
@login_required
def update_leave_status(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    user = leave.user
    year = leave.start_date.year

    leave_balance = LeaveBalance.objects.filter(user=user, current_year=year).first()

    if request.method == 'POST':
        status = request.POST.get('status')
        rejection_reason = request.POST.get('rejection_reason', '')

        # Handle approval
        if status == "Approved" and leave.status != "Approved":
            if leave.leave_type == "casual" and leave_balance.casual_leave >= leave.get_total_days():
                leave_balance.casual_leave -= leave.get_total_days()
            elif leave.leave_type == "earned" and leave_balance.earned_leave >= leave.get_total_days():
                leave_balance.earned_leave -= leave.get_total_days()
            elif leave.leave_type == "half_pay" and leave_balance.half_pay_leave >= leave.get_total_days():
                leave_balance.half_pay_leave -= leave.get_total_days()
            elif leave.leave_type == "maternity" and leave_balance.maternity_leave >= leave.get_total_days():
                leave_balance.maternity_leave -= leave.get_total_days()
            elif leave.leave_type == "paternity" and leave_balance.paternity_leave >= leave.get_total_days():
                leave_balance.paternity_leave -= leave.get_total_days()
            # Add more types if needed

            leave_balance.save()

        # Update leave status and rejection reason
        leave.status = status
        leave.rejection_reason = rejection_reason if status == "Rejected" else ''
        leave.save()

        # Create a notification for the user who applied for the leave
        notification_message = f"Your leave request from {leave.start_date} to {leave.end_date} has been {status.lower()}."
        if status == "Rejected" and rejection_reason:
            notification_message += f" Reason: {rejection_reason}"

        Notification.objects.create(
            user=user,  # The user who applied for leave
            message=notification_message,
        )

        # Success message
        messages.success(request, f"Leave status updated to {status} and user notified.")

        return redirect('admin_dashboard')

    return render(request, 'leave_management/update_leave_status.html', {
        'leave': leave,
        'leave_balance': leave_balance,
    })


#notification 
@login_required
def notifications(request):
    # Fetch all notifications for this user, newest first
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    # Optionally mark them read here or leave that for the form action
    # notifications.filter(is_read=False).update(is_read=True)

    return render(request, 'leave_management/notifications.html', {
        'notifications': notifications
    })

from django.shortcuts import get_object_or_404, redirect
from .models import Notification
from django.contrib.auth.decorators import login_required

# Mark all notifications as read
@login_required
def mark_all_read(request):
    # Mark all notifications as read for the logged-in user
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('notifications')  # Redirect back to notifications page

# Clear all notifications
@login_required
def clear_all(request):
    # Delete all notifications for the logged-in user
    Notification.objects.filter(user=request.user).delete()
    return redirect('notifications')  # Redirect back to notifications page




@login_required
@user_passes_test(is_admin)
def admin_users(request):
    users = User.objects.all()  
    return render(request, 'leave_management/admin_users.html', {'users': users})


# Helper function to check if user is admin
def is_admin(user):
    return user.is_superuser
# Add New User (Admin)
@login_required
@user_passes_test(is_admin)
def add_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ New user added successfully!")
            return redirect('admin_users')
    else:
        form = UserCreationForm()
    return render(request, 'leave_management/add_user.html', {'form': form})

# Edit Existing User (Admin)
@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = UserCreationForm(request.POST, instance=user_obj)  # Replace with an appropriate form class
        if form.is_valid():
            form.save()
            return redirect('admin_users')
    else:
        form = RegisterForm(instance=user_obj)  # Replace with an appropriate form class
    return render(request, 'leave_management/edit_user.html', {'form': form, 'user_obj': user_obj})

# Admin User Management
@login_required
def delete_user(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, id=user_id)
        if not user.is_superuser:
            user.delete()
            messages.success(request, "User deleted successfully.")
        else:
            messages.error(request, "You cannot delete a superuser.")
    return redirect('admin_users')   

@login_required
def user_dashboard(request):
    leave_balance = LeaveBalance.objects.filter(user=request.user).first()
    recent_leaves = LeaveRequest.objects.filter(user=request.user).order_by('-applied_on')[:5]
    uploaded_courses = InServiceCourse.objects.filter(user=request.user).order_by('-start_date')[:5]

    return render(request, 'leave_management/user_dashboard.html', {
        'leave_balance': leave_balance,
        'recent_leaves': recent_leaves,
        'uploaded_courses': uploaded_courses,
    })

@login_required
def base_view(request):
    # Query the unread notifications count for the logged-in user
    notif_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    # Render the base template or the appropriate template
    return render(request, 'leave_management/base.html', {
        'notif_count': notif_count,  # Pass the count to the template
    })

@login_required
def mark_notification_read(request, notif_id):
    notification = get_object_or_404(Notification, id=notif_id)
    if notification.user == request.user:
        notification.is_read = True
        notification.save()

    return redirect('notifications')  # Redirect to notifications page or wherever you want

