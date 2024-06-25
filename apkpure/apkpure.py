import json
import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import re
import sys
import cloudscraper


# Utils
from . import extractors

class ApkPure:
    def __init__(self, headers: dict | None = None) -> None:
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"
            }
        self.headers = headers
        self.query_url = "https://apkpure.com/search?q="

    def check_name(self, name):
        name = name.strip()
        if not name:
            sys.exit(
                "No search query provided!",
            )

    def __helper(self, url) -> BeautifulSoup:
        response = self.__get_response(url=url)
        # Since response could be None check and exit if it is
        if not response:
            # Exit the program with a return code of 1. Return 0 if successful
            sys.exit("Error: Response is None!")
        return BeautifulSoup(response.text, "html.parser")

    def __get_response(self, url: str, **kwargs) -> requests.Response | None:
        response = requests.get(url, self.headers)

        if response.status_code == 403:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url=url, **kwargs)

        # Return the response if the response is successful i.e status_code == 200
        return response if response.status_code == 200 else None

    

    def search_top(self, name: str) -> str | Exception:
        self.check_name(name)

        query_url = self.query_url + name
        soup_obj = self.__helper(query_url)

        # The div element
        first_div: BeautifulSoup = soup_obj.find("div", class_="first")
        # package_url for first result
        package_url = first_div.find("a", class_="first-info")

        if first_div is None:
            raise Exception("App not found")

        if package_url is None:
            package_url = first_div.find("a", class_="dd")

        result = extractors.extract_info_from_search(first_div)

        return json.dumps(result, indent=4)

    def search_all(self, name: str) -> list[dict]:
        self.check_name(name)

        url = self.query_url + name
        soup = self.__helper(url)

        first_app = soup.find("div", class_="first")

        list_of_apps = soup.find("ul", id="search-res")  # UL
        apps_in_list_of_apps = list_of_apps.find_all("li")  # LI's

        all_results = [self.extract_info_from_search(first_app)]

        for app in apps_in_list_of_apps:
            all_results.append(extractors.extract_info_from_search(app))
            
        return json.dumps(all_results, indent=4)

    def get_versions(self, name) -> str:
        first_app_from_search : dict = json.loads(self.search_top(name))
        
        version_url = str(first_app_from_search.get('package_url')) + "/versions"
        
        soup = self.__helper(version_url)
    
        versions_list : list = soup.find("ul", class_="ver-wrap")

        items : list[BeautifulSoup] = versions_list.find_all("li")
        items.pop() # Delete the last one item, cause its a bottom link
        
        all_versions : list[dict]= []
        
        for item in items:
            data : BeautifulSoup = item.find("a", class_="ver_download_link") # tag a
            
            all_versions.append(
                extractors.extract_info_from_versions(data)
            )
            
        return json.dumps(all_versions, indent=4)

    def get_info(self, name: str) -> str:
        url = json.loads(self.search_top(name))["package_url"]
        html_obj = self.__helper(url)

        divs = html_obj.find("div", class_="detail_banner")
        title = divs.find("div", class_="title_link").get_text(strip=True)
        rating = divs.find("span", class_="rating").get_text(strip=True)
        date = divs.find("p", class_="date").text.strip()
        sdk_info = divs.find("p", class_="details_sdk")
        latest_version = sdk_info.contents[1].get_text(strip=True)
        developer = sdk_info.contents[3].get_text(strip=True)
        dl_btn = divs.find("a", class_="download_apk_news").attrs
        package_name = dl_btn["data-dt-package_name"]
        package_versioncode = dl_btn["data-dt-version_code"]
        download_link = dl_btn["href"]

        # Find the Description
        description = html_obj.find("div", class_="translate-content").get_text()

        # Older Versions
        versions = json.loads(self.get_versions(name))
        new = {
            "title": title,
            "rating": rating,
            "date": date,
            "latest_version": latest_version,
            "description": description,
            "developer": developer,
            "package_name": package_name,
            "package_versioncode": package_versioncode,
            "package_url": download_link,
            "older_versions": versions,
        }
        return json.dumps(new, indent=4)

    def download(self, name: str, version: str = "") -> str | None:
        base_url = "https://d.apkpure.com/b/APK/"

        versions = json.loads(self.get_versions(name))
        url = ""
        if not version:
            url = f"{base_url}{versions[0]["app"]}?versionCode={versions[1]["version_code"]}"
            print(url)
            print("Downloading Latest")

        for v in versions[1:]:
            if version == v["version"]:
                url = f"https://d.apkpure.com/b/APK/{versions[0]["app"]}?versionCode={v["version_code"]}"
                break

        # Check url
        if not url:
            print(f"Invalid Version: {version}")
            return None
        print(f"Downloading v{version}")
        return self.downloader(url)

    # TODO Fix this downloader method
    def downloader(self, url: str) -> str:
        response = self.__get_response(
            url=url, stream=True, allow_redirects=True, headers=self.headers
        )

        d = response.headers.get("content-disposition")
        fname = re.findall("filename=(.+)", d)[0].strip('"')

        fname = os.path.join(os.getcwd(), f"apks/{fname}")

        os.makedirs(os.path.dirname(fname), exist_ok=True)

        if os.path.exists(fname) and int(
            response.headers.get("content-length", 0)
        ) == os.path.getsize(fname):
            print("File Exists!")
            return os.path.realpath(fname)

        with tqdm.wrapattr(
            open(fname, "wb"),
            "write",
            miniters=1,
            total=int(response.headers.get("content-length", 0)),
        ) as file:
            for chunk in response.iter_content(chunk_size=4 * 1024):
                if chunk:
                    file.write(chunk)

        return os.path.realpath(fname)
