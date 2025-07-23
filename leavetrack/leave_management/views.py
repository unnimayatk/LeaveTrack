from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ApplyLeaveForm, InServiceCourseForm, RegisterForm
from django.contrib.auth.models import User
from .models import LeaveBalance
from datetime import datetime
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from leave_management.models import Notification
from .models import InServiceCourse
from django.http import HttpResponse
from .models import LeaveApplication




#function to check if user is admin (MOVED UP)
def is_admin(user):
    return user.is_superuser

# Home Page
def home(request):
    return render(request, 'leave_management/home.html')


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
            messages.error(request, '❌ Invalid username or password')

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
        form = ApplyLeaveForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.user = request.user  # ✅ Assign user before save
            leave.save()

            # ✅ Notify Admin
            admins = User.objects.filter(is_superuser=True)
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    message=f"{request.user.username} submitted a leave request from {leave.start_date} to {leave.end_date}."
                )

            # ✅ Send Email
            subject = "Leave Application Submitted"
            message = f"Hi {request.user.username},\n\nYour leave request from {leave.start_date} to {leave.end_date} has been submitted successfully.\n\nThanks,\nLeaveTrack"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [request.user.email], fail_silently=True)

            messages.success(request, "Leave application submitted successfully!")
            return redirect('leave_status')
        else:
            messages.error(request, "❌ Error: Please correct the form.")
    else:
        form = ApplyLeaveForm(user=request.user)  # ✅ Include user here too

    return render(request, 'leave_management/apply_leave.html', {'form': form})


# My Leaves Page
@login_required
def my_leaves(request):
    leave_requests = LeaveApplication.objects.filter(user=request.user).order_by('-start_date')
    current_year = datetime.now().year
    leave_balance = LeaveBalance.objects.filter(user=request.user, year=current_year).first()

    return render(request, 'leave_management/my_leaves.html', {
        'leave_requests': leave_requests,
        'leave_balance': leave_balance,
        'year': current_year
    })


# Dashboard View
@login_required
def dashboard(request):
    uploaded_courses = InServiceCourse.objects.filter(user=request.user)
    return render(request, 'leave_management/dashboard.html', {
        'uploaded_courses': uploaded_courses
    })

# Leave Status Page
@login_required
def leave_status(request):
    leave_requests = LeaveApplication.objects.filter(user=request.user).order_by('-applied_on')
    return render(request, 'leave_management/leave_status.html', {'leave_requests': leave_requests})

# In-Service Course Upload
@login_required
def inservice_course(request):
    if request.method == 'POST':
        form = InServiceCourseForm(request.POST, request.FILES)
        if form.is_valid():
            inservice = form.save(commit=False)
            inservice.user = request.user
            inservice.save()
            return redirect('inservice_course')  # refresh page
    else:
        form = InServiceCourseForm()

    courses = InServiceCourse.objects.filter(user=request.user).order_by('-start_date')
    return render(request, 'leave_management/inservice_course.html', {'form': form, 'courses': courses})

# Admin Dashboard View
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_users = User.objects.count()
    total_leave_requests = LeaveApplication.objects.count()
    pending_leaves = LeaveApplication.objects.filter(status="Pending").count()
    approved_leaves = LeaveApplication.objects.filter(status="Approved").count()
    rejected_leaves = LeaveApplication.objects.filter(status="Rejected").count()

    context = {
        "total_users": total_users,
        "total_leave_requests": total_leave_requests,
        "pending_leaves": pending_leaves,
        "approved_leaves": approved_leaves,
        "rejected_leaves": rejected_leaves,
    }
    return render(request, "leave_management/admin_dashboard.html", context)


# Admin Leave Requests View
@login_required
@user_passes_test(is_admin)
@staff_member_required
def admin_leave_requests(request):
    leave_requests = LeaveApplication.objects.all().order_by('-applied_on')
    return render(request, 'leave_management/admin_leave_requests.html', {
        'leave_requests': leave_requests
    })

@login_required
@user_passes_test(is_admin)
def admin_users(request):
    users = User.objects.all()  
    return render(request, 'leave_management/admin_users.html', {'users': users})


# Helper function to check if user is admin
def is_admin(user):
    return user.is_superuser

# Approve Leave Request
@login_required
@user_passes_test(is_admin)
def approve_leave(request, leave_id):
    try:
        leave = LeaveApplication.objects.get(id=leave_id)
        leave.status = "Approved"
        leave.save()
        messages.success(request, "✅ Leave Approved Successfully!")
    except LeaveApplication.DoesNotExist:
        messages.error(request, "❌ Leave Application Not Found!")

    return redirect("admin_leave_requests")  


# Reject Leave
@login_required
@user_passes_test(is_admin)
def reject_leave(request, leave_id):
    leave = get_object_or_404(LeaveApplication, id=leave_id)
    leave.status = "Rejected"
    leave.save()
    messages.error(request, "❌ Leave Rejected Successfully!")
    return redirect('admin_leave_requests')

# Approve/Reject Leave (POST Based)
@login_required
@user_passes_test(is_admin)
def approve_reject_leave(request, leave_id):
    leave = get_object_or_404(LeaveApplication, id=leave_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            leave.status = 'Approved'
            messages.success(request, "✅ Leave Approved Successfully!")
        elif action == 'reject':
            leave.status = 'Rejected'
            messages.error(request, "❌ Leave Rejected Successfully!")
        else:
            messages.error(request, "❌ Invalid action.")

        leave.save()

    return redirect('admin_leave_requests')


#update leave status (for admin)
@login_required
def update_leave_status(request, pk):
    leave = get_object_or_404(LeaveApplication, pk=pk)

    if request.method == 'POST':
        status = request.POST.get('status')
        leave.status = status
        leave.save()

        # ✅ Create Notification
        Notification.objects.create(
            user=leave.user,
            message=f"Your leave request from {leave.start_date} to {leave.end_date} has been {leave.status.lower()}."
        )

        # ✅ Send Email
        subject = "Leave Status Updated"
        message = f"Hi {leave.user.username},\n\nYour leave request from {leave.start_date} to {leave.end_date} has been {leave.status}.\n\nRegards,\nLeaveTrack"
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [leave.user.email], fail_silently=True)

        messages.success(request, "✅ Leave status updated successfully!")
        return redirect('admin_leave_requests')

    return render(request, 'leave_management/update_leave_status.html', {'leave': leave})

    
@login_required
def admin_leave_requests(request):
    leave_requests = LeaveApplication.objects.all().order_by('-applied_on')
    return render(request, 'leave_management/admin_leave_requests.html', {'leave_requests': leave_requests})

# 📥 Notifications View
@login_required
def notifications(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-timestamp')
    notifs.update(is_read=True)  # ✅ Fix here
    return render(request, 'leave_management/notifications.html', {'notifications': notifs})

# 🗑️ Clear All Notifications
@login_required
def clear_notifications(request):
    Notification.objects.filter(user=request.user).delete()
    return redirect('notifications')


# ✅ Mark One as Read
@login_required
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    return redirect('notifications')


@login_required
def test_email(request):
    send_mail(
        subject='Test Email from LeaveTrack',
        message='🎉 Your email settings are working!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[request.user.email],
        fail_silently=False,
    )
    return HttpResponse("✅ Test email sent successfully to your inbox.")
