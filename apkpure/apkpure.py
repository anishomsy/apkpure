import json
import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import re

import cloudscraper


class ApkPure:
    def __init__(self, headers: dict | None = None) -> None:
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"
            }
        self.headers = headers
        self.query_url = "https://apkpure.com/search?q="


    def __helper(self, url) -> BeautifulSoup:
        response = self.get_response(url=url)
        return BeautifulSoup(response.text, "html.parser")

    def get_response(self, url: str, **kwargs) -> requests.Response | None:
        response = requests.get(url, self.headers)

        if response.status_code == 403:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url=url, **kwargs)

        # Return the response if the response is successful i.e status_code == 200
        return response if response.status_code == 200 else None
    
    def extract_info(self, div_element):
        def get_basic_info() -> dict:
            title = div_element.find("p", class_="p1")
            developer = div_element.find("p", class_="p2")
            return {
                'title' : title.text.strip() if title else 'Uknown',
                'developer' : developer.text.strip() if developer else 'Uknown',
            }
            
        def get_package_url(div_element) -> dict:
            package_url = div_element.find("a", class_="first-info")
            
            if package_url is None:
                package_url = div_element.find("a", class_="dd")
            
            return {
                "package_url" : package_url.attrs.get('href', 'Uknown')
            }
            
        def get_icon() -> dict:
            icon = div_element.find("img")

            return {
                'icon' : icon.attrs.get('src', 'Uknown') if icon else 'Uknown'
                }
            
        def get_package_data() -> dict:
            # This method work if is the first element
            package_data = div_element.attrs
            print(bool(package_data), package_data)
            
            if not package_data:
                print('verdade')
                # If the div in the div_element is not the correct, so its a li element
                package_data = div_element.find("a", class_="is-download")
            
            package_name = package_data.get("data-dt-app", 'Uknown')
            package_size = package_data.get("data-dt-filesize", 'Uknown')
            package_version = package_data.get("data-dt-version", 'Uknown')
            package_version_code = package_data.get("data-dt-versioncode", 'Uknown')

            return {
                "package_name" : package_name,
                "package_size" : package_size,
                "package_version" : package_version,
                "package_version_code" : package_version_code
            }
            
        def get_download_link() -> dict:
            if download_link := div_element.find("a", class_="is-download"):
                return {
                    'download_link' : download_link.attrs.get('href', 'Uknown')
                }

            download_link = div_element.find("a", class_="da")

            return {
                'download_link' : download_link.attrs.get('href', 'Uknown')
            }
            
        basic_info : dict = get_basic_info()
        package_url : dict = get_package_url(div_element)
        icon : dict = get_icon()
        package_data : dict = get_package_data()
        download_link : dict = get_download_link()

        # Spread all the info into the all_info and then dump it to json
        all_app_info = basic_info | icon | package_data | download_link | package_url
        
        return all_app_info


    def search_top(self, name: str) -> str | Exception:
        query_url = self.query_url + name
        soup_obj = self.__helper(query_url)
        
        # The div element
        first_div : BeautifulSoup = soup_obj.find("div", class_="first")
        # package_url for first result
        package_url = first_div.find("a", class_="first-info")

        if first_div is None:
            raise Exception("App not found")
        
        
        if package_url is None:
            package_url = first_div.find("a", class_="dd")

        result = self.extract_info(first_div)

        return json.dumps(result)


    def search_all(self, name: str) -> BeautifulSoup:
        url = self.query_url + name
        soup = self.__helper(url)
        
        first_app = soup.find("div", class_="first")
        list_of_apps = soup.find("ul", class_="search-res")
        
        apps_in_result = list_of_apps.find_all("li")
        
        return self.extract_info(apps_in_result[0])
        

        return self.__helper(url)

    def get_versions(self, name) -> str:
        s = json.loads(self.search_top(name))
        url = f"{s["package_url"]}/versions"
        soup = self.__helper(url)

        full = [{"app": s["package_name"]}]
        ul = soup.find("ul", class_="ver-wrap")
        lists = ul.find_all("li")
        lists.pop()
        for li in lists:
            dl_btn = li.find("a", class_="ver_download_link").attrs
            package_version = dl_btn["data-dt-version"]
            download_link = dl_btn["href"]

            package_versioncode = dl_btn["data-dt-versioncode"]

            new = {
                "version": package_version,
                "download_link": download_link,
                "version_code": package_versioncode,
            }
            full.append(new)
        return json.dumps(full)

    def get_info(self, name: str) -> str:
        url = json.loads(self.search_top(name))["package_url"]
        soup = self.__helper(url)

        divs = soup.find("div", class_="detail_banner")
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
        description = soup.find("div", class_="translate-content").get_text()

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
        return json.dumps(new)

    def download(self, name: str, version: str = "") -> str | None:
        base_url = "https://d.apkpure.com/b/APK/"
        base_url_XAPK = "https://d.apkpure.com/b/XAPK/"

        versions = json.loads(self.get_versions(name))
        url = ""
        if not version:
            url = f"{base_url}{versions[0]["app"]}?versionCode={versions[1]["version_code"]}"
            print(url)
            print("Downloading Latest")
            try:
                callback = self.downloader(url)
            except KeyError:
                url = f"{base_url_XAPK}{versions[0]["app"]}?versionCode={versions[1]["version_code"]}"
                return self.downloader(url)

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
        response = self.get_response(url = url , stream=True, allow_redirects=True, headers=self.headers)

        d = response.headers.get("content-disposition")
        fname = re.findall("filename=(.+)", d)[0].strip('"')

        fname = os.path.join(os.getcwd(), f"apks/{fname}")

        os.makedirs(os.path.dirname(fname), exist_ok=True)

        if os.path.exists(fname) and int(response.headers.get("content-length", 0)) == os.path.getsize(fname):
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
