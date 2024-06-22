from apkpure.apkpure import ApkPure


api = ApkPure()


# allResults = api.download("facebook lite")
# print(allResults)
top_result = api.search_top("WhatsApp")
print(top_result)
#
# #
# # Search for all results
#
# all_results = api.search_all("Tiktok")
# print(all_results)
# #
# #
# Get app versions
# versions = api.get_versions("WhatsApp")
# print(versions)
#
# # Get app info
# app_info = api.get_info("WhatsApp")
# print(app_info)

# Download the latest version of an app
# print(api.download("facebook lite"))
# print(os.path.getsize("./WhatsApp Messenger_2.24.13.9_APKPure.apk"))
# Download a specific version of an app
# api.download("WhatsApp", version="3.21.1.15")
