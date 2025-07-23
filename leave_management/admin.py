from django.contrib import admin
from .models import LeaveRequest, LeaveBalance, InServiceCourse
from django.utils.html import format_html


# ✅ Customizing Leave Request Admin
@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'leave_type')
    search_fields = ('user__username', 'leave_type')
    actions = ['approve_selected', 'reject_selected']
    
    def approve_selected(self, request, queryset):
        for leave in queryset:
            leave.status = 'approved'
            leave.save()  # this will call the save method that updates balance
    approve_selected.short_description = "Approve selected leaves"

    def reject_selected(self, request, queryset):
        for leave in queryset:
            leave.status = 'rejected'
            leave.save()
    reject_selected.short_description = "❌ Reject selected leaves"



# ✅ LeaveBalance Admin
@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'casual_leave', 'earned_leave',
        'half_pay_leave', 'maternity_leave', 'paternity_leave'
    )
    list_editable = ('casual_leave', 'earned_leave')
    search_fields = ('user__username',)

# ✅ Customizing In-Service Course Admin
@admin.register(InServiceCourse)
class InServiceCourseAdmin(admin.ModelAdmin):
    list_display = ('course_name', 'user', 'course_type', 'start_date', 'end_date', 'certificate', 'uploaded_at')
    list_filter = ('course_type', 'start_date', 'end_date')
    search_fields = ('course_name', 'user__username')
    readonly_fields = ('uploaded_at',)

    # Optional: Make certificate clickable in list view
    def certificate_link(self, obj):
        if obj.certificate:
            return format_html('<a href="{}" target="_blank">View Certificate</a>', obj.certificate.url)
        return "No certificate uploaded"
    certificate_link.short_description = 'Certificate'
