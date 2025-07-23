from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from leave_management.models import LeaveBalance

@receiver(post_save, sender=User)
def create_leave_balance(sender, instance, created, **kwargs):
    """ Automatically create LeaveBalance when a new user registers. """
    if created:
        LeaveBalance.objects.create(user=instance)
