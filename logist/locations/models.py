from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
# from .services.opening_hours import get_site_hours

# -----------------------
# Country Level
# -----------------------
class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=5, unique=True)  # e.g., 'DE', 'AT'

    class Meta:
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name

# -----------------------
# Region Level
# -----------------------
class Region(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='regions')

    def __str__(self):
        return f"{self.name}, {self.country.code}"

# -----------------------
# Location Level (city/town/village)
# -----------------------
class Location(models.Model):
    name = models.CharField(max_length=100)  # city, town, or municipality
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='locations')

    def __str__(self):
        return f"{self.name} ({self.region})"


# -----------------------
# Company
# -----------------------
class Company(models.Model):
    name = models.CharField(max_length=100)  # company name
    
    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name


# -----------------------
# Site Level (physical branch/office)
# -----------------------
class Site(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sites', null=True)
    name = models.CharField(max_length=200,blank=True, null=True)  # branch/site name
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='sites')
    address = models.TextField(blank=True, null=True)
    zip_code = models.CharField(
        max_length=10,
        validators=[RegexValidator(
            r'^\d{5}$',
            message="Enter a valid 5-digit German ZIP code."
        )],
        blank=True,
        null=True
    )
    google_place_id = models.CharField(max_length=200, blank=True, null=True)
    """
    def get_opening_hours(self, check_date):
        # Same logic as before
        exception = self.exceptions.filter(date=check_date).first()
        if exception:
            if exception.open_time and exception.close_time:
                return exception.open_time, exception.close_time
            return None, None

        holidays = PublicHoliday.objects.filter(
            date=check_date,
            country=self.location.region.country
        ).filter(models.Q(region__isnull=True) | models.Q(region=self.location.region))
        
        if holidays.exists():
            return None, None

        weekday = check_date.weekday()
        default_hours = self.default_hours.filter(weekday=weekday).first()
        if default_hours:
            return default_hours.open_time, default_hours.close_time

        return None, None
    """
    def get_site_hours(site: "Site", check_date):
        # 1. Check for SiteException
        exception = site.exceptions.filter(date=check_date).first()
        if exception:
            if exception.open_time and exception.close_time:
                return exception.open_time, exception.close_time
            return None, None  # Closed

        # 2. Check PublicHoliday
        holidays = PublicHoliday.objects.filter(
            date=check_date,
            country=site.location.region.country
        ).filter(models.Q(region__isnull=True) | models.Q(region=site.location.region))
        if holidays.exists():
            return None, None  # Closed

        # 3. DefaultHours
        weekday = check_date.weekday()
        default_hours = site.default_hours.filter(weekday=weekday).first()
        if default_hours:
            if getattr(default_hours, "is_closed", False):
                return None, None
            return default_hours.open_time, default_hours.close_time

        # 4. If nothing exists, assume closed
        return None, None

    @property
    def today_hours(self):
        from datetime import date
        return self.get_opening_hours(date.today())
    
    def __str__(self):
        return f"{self.company.name} - {self.location.name} - {self.name}"


WEEKDAYS = [
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
    (6, 'Sunday'),
]


class DefaultHours(models.Model):
    site = models.ForeignKey('Site', on_delete=models.CASCADE, related_name='default_hours')
    weekday = models.IntegerField(choices=WEEKDAYS)
    open_time = models.TimeField(blank=True, null=True)
    close_time = models.TimeField(blank=True, null=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('site', 'weekday')  # one entry per day per site

    def __str__(self):
        if self.is_closed:
            return f"{self.site.name} - {self.get_weekday_display()}: Closed"
        return f"{self.site.name} - {self.get_weekday_display()}: {self.open_time}-{self.close_time}"

class SiteException(models.Model):
    site = models.ForeignKey('Site', on_delete=models.CASCADE, related_name='exceptions')
    date = models.DateField()
    open_time = models.TimeField(blank=True, null=True)
    close_time = models.TimeField(blank=True, null=True)
    reason = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        unique_together = ('site', 'date')

    def __str__(self):
        status = f"{self.open_time}-{self.close_time}" if self.open_time and self.close_time else "Closed"
        return f"{self.site.name} ({self.date}): {status} - {self.reason}"
    

class PublicHoliday(models.Model):
    country = models.ForeignKey('Country', on_delete=models.CASCADE, related_name='holidays')
    region = models.ForeignKey('Region', on_delete=models.CASCADE, blank=True, null=True, related_name='holidays')
    date = models.DateField()
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = ('country', 'region', 'date')

    def __str__(self):
        scope = self.region.name if self.region else self.country.name
        return f"{self.name} ({scope}): {self.date}"

