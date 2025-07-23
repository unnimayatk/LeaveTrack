from django.contrib import admin
from .models import LeaveRequest, LeaveBalance, InServiceCourse, LeaveApplication

# ✅ Customizing Leave Request Admin
@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'start_date', 'end_date', 'status', 'approve_leave', 'reject_leave')
    list_filter = ('status', 'leave_type')
    search_fields = ('user__username', 'leave_type')
    actions = ['approve_selected', 'reject_selected']

    def approve_leave(self, obj):
        return "✅ Approve"
    approve_leave.short_description = 'Approve'

    def reject_leave(self, obj):
        return "❌ Reject"
    reject_leave.short_description = 'Reject'

    def approve_selected(self, request, queryset):
        queryset.update(status='approved')
    approve_selected.short_description = "Approve selected leaves"

    def reject_selected(self, request, queryset):
        queryset.update(status='rejected')
    reject_selected.short_description = "Reject selected leaves"


# ✅ Customizing Leave Balance Admin
@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'casual_leave', 'earned_leave', 'half_pay_leave', 'maternity_leave', 'paternity_leave')

# ✅ Customizing In-Service Course Admin
@admin.register(InServiceCourse)
class InServiceCourseAdmin(admin.ModelAdmin):
    list_display = ('course_type', 'course_name', 'start_date', 'end_date', 'certificate')

# ✅ Customizing Leave Application Admin
@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'leave_type')
    search_fields = ('user__username', 'leave_type')
