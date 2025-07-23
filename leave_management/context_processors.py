# leave_management/context_processors.py

from .models import Notification
from .models import InServiceCourse

def notification_count(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'notif_count': count}
    return {'notif_count': 0}

def inservice_courses_for_user(request):
    if request.user.is_authenticated:
        courses = InServiceCourse.objects.filter(user=request.user).order_by('-id')
        return {'sidebar_courses': courses}
    return {}
