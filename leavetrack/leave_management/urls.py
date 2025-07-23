from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('apply_leave/', views.apply_leave, name='apply_leave'),
    path('leave_status/', views.leave_status, name='leave_status'),
    path('my_leaves/', views.my_leaves, name='my_leaves'),
    path('inservice_course/', views.inservice_course, name='inservice_course'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),    
    path('admin_leave_requests/', views.admin_leave_requests, name='admin_leave_requests'),  # ✅ This must exist
    path('admin_users/', views.admin_users, name='admin_users'),
    path('approve_leave/<int:leave_id>/', views.approve_leave, name='approve_leave'),
    path('reject_leave/<int:leave_id>/', views.reject_leave, name='reject_leave'),
    path('leave/action/<int:leave_id>/', views.approve_reject_leave, name='approve_reject_leave'),
    path('update-leave-status/<int:pk>/', views.update_leave_status, name='update_leave_status'),
    path('admin_leave_requests/', views.admin_dashboard, name='admin_leave_requests_approve'),  # ✅ This must exist
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/clear/', views.clear_notifications, name='clear_notifications'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('test-email/', views.test_email, name='test_email'),

]
