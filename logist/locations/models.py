from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from itertools import groupby
# from .services.opening_hours import get_site_hours


class Weekday:
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    CHOICES = [
        (MONDAY, "Monday"),
        (TUESDAY, "Tuesday"),
        (WEDNESDAY, "Wednesday"),
        (THURSDAY, "Thursday"),
        (FRIDAY, "Friday"),
        (SATURDAY, "Saturday"),
        (SUNDAY, "Sunday"),
    ]

    SHORT_NAMES = ["Mo","Di","Mi","Do","Fr","Sa","So"]

    @classmethod
    def short_name(cls, weekday_int):
        return cls.SHORT_NAMES[weekday_int]

# -----------------------
# Country Level
# -----------------------
class Country(models.Model):
    name = models.CharField(max_length=100)
    local_name = models.CharField(max_length=100, blank=True, null=True)
    german_name = models.CharField(max_length=100, blank=True, null=True)
    code = models.CharField(max_length=5, unique=True,blank=True, null=True)  # e.g., 'DE', 'AT'
    dialing_code = models.CharField(max_length=5, blank=True, null=True)
    # time_zones = models.CharField(max_length=100)
    # time_zones = models.CharField(max_length=100)
    emoji_flag = models.CharField(max_length=10, blank=True, null=True)  # 4–10 is usually enough for flags + complex emoji

    class Meta:
        verbose_name_plural = "Countries"

    def __str__(self):
        # return self.name
        return f"{self.emoji_flag}{self.name}"

# -----------------------
# Region Level
# -----------------------
class Region(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='regions')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name}, {self.country.code}"

# -----------------------
# Location Level (city/town/village)
# -----------------------
class Location(models.Model):
    name = models.CharField(max_length=100)  # city, town, or municipality
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='locations')

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'region')  # only one location per region

    def __str__(self):
        return f"{self.name} ({self.region})"

# -----------------------
# Group
# -----------------------
class Group(models.Model):
    name = models.CharField(max_length=100)  # group name

    def __str__(self):
        return self.name

# -----------------------
# Company
# -----------------------
class Company(models.Model):
    name = models.CharField(max_length=100)  # company name
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, related_name='companies', blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['name']  # alphabetical by name

    def __str__(self):
        return self.name

"""
WEEKDAY_NAMES = ["Mo","Tu","We","Th","Fr","Sa","Su"]
"""
# -----------------------
# Site Level (physical branch/office)
# -----------------------
class Site(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sites', null=True)
    name = models.CharField(max_length=200, blank=True, null=True)  # branch/site name
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
    email = models.EmailField(max_length=254, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
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
    """
    @property
    def hours_display(self):

        Returns a human-readable opening hours string like:
        "Mo–Fr 08:00–17:00; Sa 08:00–11:00"


        # 1️⃣ get all opening hours for this site, ordered by weekday
        hours = self.default_hours.order_by('weekday')

        # 2️⃣ convert each to (weekday_name, open-close string)
        # hours_list = [(WEEKDAY_NAMES[h.weekday], f"{h.open_time.strftime('%H:%M')}-{h.close_time.strftime('%H:%M')}") for h in hours]
        # Weekday.short_name(h.weekday)
        hours_list = [(Weekday.short_name(h.weekday), f"{h.open_time.strftime('%H:%M')}-{h.close_time.strftime('%H:%M')}") for h in hours]


        # 3️⃣ group consecutive days with same hours
        result = []
        for k, g in groupby(enumerate(hours_list), key=lambda x: x[1][1]):
            group = list(g)
            # extract weekdays
            days = [x[1][0] for x in group]
            if len(days) == 1:
                day_str = days[0]
            else:
                day_str = f"{days[0]}–{days[-1]}"
            result.append(f"{day_str} {k}")

        return "; ".join(result)
    """

    @property
    def hours_display(self):
        """
        Returns a human-readable opening hours string like:
        "Mo–Fr 08:00–17:00; Sa Closed"
        """

        # 1) Get all opening hours ordered by weekday
        hours = self.default_hours.order_by("weekday")

        # 2) Build hours_list with correct logic:
        #    - Explicit closure
        #    - Normal hours
        #    - Unknown
        hours_list = []

        for h in hours:
            wd = Weekday.short_name(h.weekday)

            if getattr(h, "is_closed", False):
                hours_list.append((wd, "Closed"))
            elif h.open_time and h.close_time:
                hours_list.append(
                    (wd, f"{h.open_time.strftime('%H:%M')}-{h.close_time.strftime('%H:%M')}")
                )
            else:
                hours_list.append((wd, "Unknown"))
        
        # 2b) If all hours are Unknown, return empty string
        if all(hour == "Unknown" for _, hour in hours_list):
            return ""
        
        # 3) Group consecutive days with same hours
        result = []
        for key, group in groupby(enumerate(hours_list), key=lambda x: x[1][1]):
            group = list(group)
            days = [x[1][0] for x in group]

            if len(days) == 1:
                day_str = days[0]
            else:
                day_str = f"{days[0]}–{days[-1]}"

            result.append(f"{day_str} {key}")

        return "; ".join(result)

    
    class Meta:
        ordering = ['location']
        unique_together = ('location', 'company', 'name')  # one site per company per location, otherwise distinct names

    @property
    def today_hours(self):
        from datetime import date
        return Site.get_site_hours(self, date.today())
        # return self.get_opening_hours(date.today())
    
    def export_to_JSON():
        data = []
        for site in Site.objects.all().select_related("company"):
            parts = []
            if site.company.group:
                parts.append(site.company.group.name)
            else:
                parts.append(site.company.name)
            parts.append(site.location.name)
            if site.name:
                parts.append(site.name)
            name = " - ".join(parts)
            data.append({
                "company": site.company.name,
                "name": name,
                "address": site.address,
                "maps_link": "",
                "phone": site.phone,
                "hours": site.hours_display,
            })
        
        data.sort(key=lambda x: x["company"])

        import json
        from pathlib import Path

        # Path to the development folder inside your project
        dev_folder = Path("/Users/marincordeleanu/code/github/pilot/data")
        json_file_path = dev_folder / "sites_data.json"
        # Write JSON file
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"JSON exported to {json_file_path}")


    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company.name} - {self.location.name} - {self.name}"

"""
WEEKDAYS = [
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
    (6, 'Sunday'),
]
"""
class DefaultHours(models.Model):
    site = models.ForeignKey('Site', on_delete=models.CASCADE, related_name='default_hours')
    # weekday = models.IntegerField(choices=WEEKDAYS)
    weekday = models.IntegerField(choices=Weekday.CHOICES)
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

