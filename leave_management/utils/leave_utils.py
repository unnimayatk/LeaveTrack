from datetime import timedelta
from leave_management.models import Holiday

def get_prefixed_holidays(start_date):
    """Return a list of consecutive holiday dates immediately before `start_date`."""
    dates = []
    current = start_date - timedelta(days=1)
    while Holiday.objects.filter(date=current).exists():
        dates.insert(0, current)    # prepend so earliest date is first
        current -= timedelta(days=1)
    return dates

def get_suffixed_holidays(end_date):
    """Return a list of consecutive holiday dates immediately after `end_date`."""
    dates = []
    current = end_date + timedelta(days=1)
    while Holiday.objects.filter(date=current).exists():
        dates.append(current)
        current += timedelta(days=1)
    return dates
