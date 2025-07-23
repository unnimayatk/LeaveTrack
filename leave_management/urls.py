from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard_redirect_view, name='dashboard'),
    path('apply_leave/', views.apply_leave, name='apply_leave'),
    path('leave_status/', views.leave_status, name='leave_status'),
    path('my_leaves/', views.my_leaves, name='my_leaves'),
    path('inservice_course/', views.inservice_course, name='inservice_course'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),   
    path('admin_leave_requests/', views.admin_leave_requests, name='admin_leave_requests'),  # ✅ This must exist
    path('admin_users/', views.admin_users, name='admin_users'),
    path('approve_leave/<int:leave_id>/', views.approve_leave, name='approve_leave'),
    path('reject_leave/<int:leave_id>/', views.reject_leave, name='reject_leave'),
    path('leave/action/<int:leave_id>/', views.approve_reject_leave, name='approve_reject_leave'),
    path("update-leave-status/<int:leave_id>/", views.update_leave_status, name="update_leave_status"),
    path('admin_leave_requests/', views.admin_dashboard, name='admin_leave_requests_approve'),  # ✅ This must exist
    path('notifications/', views.notifications, name='notifications'),
    path('mark_all_read/', views.mark_all_read, name='mark_all_read'),
    path('clear_all/', views.clear_all, name='clear_all'),
    path('admin/users/add/', views.add_user, name='add_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('dashboard/certificates/', views.admin_certificates_view, name='admin_certificates'),
    path('admin/certificates/edit/<int:pk>/', views.edit_certificate, name='edit_certificate'),
    path('admin/certificates/delete/<int:pk>/', views.delete_certificate, name='delete_certificate'),

    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='leave_management/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='leave_management/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='leave_management/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='leave_management/password_reset_complete.html'), name='password_reset_complete'),
    
]