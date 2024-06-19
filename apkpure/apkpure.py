import json
import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import re

import cloudscraper


class ApkPure:
    def __init__(
        self,
        headers: dict | None = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"
        },
    ) -> None:
        self.headers = headers

    def __helper(self, url):
        response = self.get_response(url=url)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup

    def get_response(self, url: str, **kwargs):
        response = requests.get(url, self.headers)

        if response.status_code == 403:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url=url, **kwargs)

        # Return the response if the response is successful i.e status_code == 200
        # TODO fix the error handle inside the function or create another one to show a message that the server is blocked
        return response if response.status_code == 200 else None

    def search_top(self, name: str) -> str | Exception:
        url = f"https://apkpure.com/search?q={name}"
        soup = self.__helper(url)
        try:
            result = soup.find("div", class_="first")
            package_url = result.find("a", class_="first-info").attrs["href"]
        except Exception:
            return Exception("Invalid app name!")

        title = result.find("p", class_="p1").text.strip()
        developer = result.find("p", class_="p2").text.strip()
        icon = result.find("img").attrs["src"]
        dl_btn = result.attrs
        package_name = dl_btn["data-dt-app"]
        package_size = dl_btn["data-dt-filesize"]
        package_version = dl_btn["data-dt-version"]
        package_version_code = dl_btn["data-dt-versioncode"]

        try:
            download_link = result.find("a", class_="is-download").attrs["href"]
        except:
            download_link = result.find("a", class_="da").attrs["href"]

        package = {
            "title": title,
            "developer": developer,
            "package_name": package_name,
            "package_url": package_url,
            "icon": icon,
            "version": package_version,
            "version_code": package_version_code,
            "size": package_size,
            "download_link": download_link,
        }
        return json.dumps(package)

    def search_all(self, name: str) -> str:
        full = []

        url = f"https://apkpure.com/search?q={name}"

        try:
            first = self.search_top(name)
            full.append(json.loads(first))
        except Exception:
            full = []
        soup = self.__helper(url)
        try:
            first = soup.find("div", class_="")
        except Exception as e:
            raise
        try:
            results = soup.find("div", class_="list sa-apps-div app-list")
            ul = results.find_all("li")
        except:
            results = soup.find(
                "div", class_="list sa-apps-div show-top-stroke app-list"
            )
            ul = results.find_all("li")
        for li in ul:
            package_url = li.find("a", class_="dd", href=True).attrs["href"]
            title = li.find("p", class_="p1").text.strip()
            developer = li.find("p", class_="p2").text.strip()
            icon = li.find("img").attrs["src"]
            dl_btn = li.find("a", class_="is-download").attrs
            package_name = dl_btn["data-dt-app"]
            package_size = dl_btn["data-dt-filesize"]
            package_version = dl_btn["data-dt-version"]
            package_versioncode = dl_btn["data-dt-versioncode"]
            download_link = dl_btn["href"]

            new = {
                "title": title,
                "developer": developer,
                "package_name": package_name,
                "package_url": package_url,
                "icon": icon,
                "version": package_version,
                "version_code": package_versioncode,
                "size": package_size,
                "download_link": download_link,
            }
            full.append(new)
        return json.dumps(full)

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
        
        # Some apps only exist as xapk file, and if we try to get the base url as APK the script will get error
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

        if os.path.exists(fname):
            if int(response.headers.get("content-length", 0)) == os.path.getsize(fname):
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
