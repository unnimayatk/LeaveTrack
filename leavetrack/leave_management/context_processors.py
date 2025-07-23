# leave_management/context_processors.py

from .models import Notification
from .models import InServiceCourse

def notification_count(request):
    if request.user.is_authenticated:
        notif_count = Notification.objects.filter(user=request.user, seen=False).count()
    else:
        notif_count = 0
    return {'notif_count': notif_count}



def inservice_courses_for_user(request):
    if request.user.is_authenticated:
        courses = InServiceCourse.objects.filter(user=request.user).order_by('-id')
        return {'sidebar_courses': courses}
    return {}
