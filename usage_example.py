"""
This file is to support you to use the apkpure api
"""

# Import the API
from apkpure.apkpure import ApkPure

API = ApkPure()

# Get the first result from app
top_result = API.get_first_app_result('App Name')

# Get all apps from result
all_results = API.get_all_apps_results('App Name')

# Get info from an app
app_info = API.get_info('App Name')

# Get the versions of an app
versions = API.get_versions('App Name')

# Downlaod an app
API.download('App Name')