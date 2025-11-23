from datetime import date
from django.db.models import Q
from ..models import Site, PublicHoliday

def get_site_hours(site: Site, check_date: date):
    """
    Returns the opening and closing time for a given site on a given date.
    Priority:
      1. SiteException
      2. PublicHoliday
      3. DefaultHours
    Returns (open_time, close_time) or (None, None) if closed.
    """
    # 1. Check for site-specific exception
    exception = site.exceptions.filter(date=check_date).first()
    if exception:
        if exception.open_time and exception.close_time:
            return exception.open_time, exception.close_time
        return None, None  # Closed

    # 2. Check for public holidays (country-wide or region-specific)
    holidays = PublicHoliday.objects.filter(
        date=check_date,
        country=site.location.region.country
    ).filter(Q(region__isnull=True) | Q(region=site.location.region))
    if holidays.exists():
        return None, None  # Closed on holiday

    # 3. Default weekly schedule
    weekday = check_date.weekday()  # 0 = Monday
    default_hours = site.default_hours.filter(weekday=weekday).first()
    if default_hours:
        return default_hours.open_time, default_hours.close_time

    return None, None  # No schedule defined