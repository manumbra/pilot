from django.contrib import admin
from .models import Country, Region, Location, Group, Company, Site, DefaultHours, SiteException, PublicHoliday

# -----------------------
# Country admin
# -----------------------
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'emoji_flag')
    search_fields = ('name', 'code')

# -----------------------
# Region admin
# -----------------------
@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    list_filter = ('country',)
    search_fields = ('name',)

# -----------------------
# Location admin
# -----------------------
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'region')
    list_filter = ('region',)
    search_fields = ('name',)

# -----------------------
# Group admin
# -----------------------
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# -----------------------
# Company admin
# -----------------------
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# -----------------------
# DefaultHours inline
# -----------------------
"""
class DefaultHoursInline(admin.TabularInline):
    model = DefaultHours
    extra = 7  # one row per weekday
    min_num = 7
    max_num = 7
"""
class DefaultHoursInline(admin.TabularInline):
    model = DefaultHours
    extra = 0  # we'll pre-fill weekdays manually
    min_num = 7
    max_num = 7
    fields = ('weekday', 'open_time', 'close_time', 'is_closed')
    readonly_fields = ('weekday',)  # prevent changing weekday manually if desired

    def get_queryset(self, request):
        """
        Pre-populate all 7 weekdays if they don't exist yet.
        """
        qs = super().get_queryset(request)
        site = getattr(self.parent_model, 'instance', None)
        if site:
            existing_days = qs.values_list('weekday', flat=True)
            for day_index, day_name in WEEKDAYS:
                if day_index not in existing_days:
                    DefaultHours.objects.create(site=site, weekday=day_index, is_closed=False)
        return qs
# -----------------------
# SiteException inline
# -----------------------
class SiteExceptionInline(admin.TabularInline):
    model = SiteException
    extra = 1

# -----------------------
# Site admin
# -----------------------
@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('company', 'location', 'name', 'address', 'zip_code')
    list_filter = ('company', 'location__region__country', 'location__region', 'location')
    search_fields = ('name', 'address', 'zip_code')
    inlines = [DefaultHoursInline, SiteExceptionInline]

# -----------------------
# PublicHoliday admin
# -----------------------
@admin.register(PublicHoliday)
class PublicHolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'country', 'region')
    list_filter = ('country', 'region', 'date')
    search_fields = ('name',)