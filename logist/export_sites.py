import json
from pathlib import Path
from locations.models import Site  # replace with your app name

import os
import sys
from pathlib import Path
import django
import json


# ─── Set DJANGO_SETTINGS_MODULE before importing anything from Django ───
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pilot.settings")  # replace 'pilot.settings'

# ─── Initialize Django ───
django.setup()

# ─── Now you can safely import your models ───
from locations.models import Site  # replace 'locations' with your app name

# Path to the development folder inside your project
dev_folder = Path("/Users/marincordeleanu/code/github/pilot/data")
# dev_folder.mkdir(parents=True, exist_ok=True)  # creates folder if it doesn't exist

json_file_path = dev_folder / "sites_data.json"

# Collect data
data = []
for site in Site.objects.all():
    name = ''
    if site.company.group:
        name.append(site.company.group.name)
    else:
        name.append(site.company.name)
    name.append(' - ')
    name.append(site.location.name)
    if site.name:
        name.append(' - ')
        name.append(site.name)
    data.append({
        "company": site.company.name,
        "name": name,
        "address": site.address,
        "maps_link": "",
        "phone": site.phone,
        "hours": site.hours_display,
    })

# Write JSON file
with open(json_file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"JSON exported to {json_file_path}")