from apkpure.apkpure import ApkPure


api = ApkPure()


allResults = api.download('free fire')
print(allResults)
# top_result = api.search_top("WhaftsApp")
# print(top_result)
#
# # Search for all results

<<<<<<< HEAD
#all_results = api.search_all("
#            download_link =  result.find("a")
#")
#print(all_results)
=======
# all_results = api.search_all("WhdsatsApp")
# print(all_results)
>>>>>>> 6956624 (testing)
#
# # Get app versions
# versions = api.get_versions("WhatsApp")
# print(versions)
#
# # Get app info
# app_info = api.get_info("WhatsApp")
# print(app_info)
#
# Download the latest version of an app
print(api.download("free fire"))
# print(os.path.getsize("./WhatsApp Messenger_2.24.13.9_APKPure.apk"))
# Download a specific version of an app
# api.download("WhatsApp", version="3.21.1.15")
