from django.apps import AppConfig

class LeaveManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'leave_management'

    def ready(self):
        import leave_management.signals  # Connects signals
