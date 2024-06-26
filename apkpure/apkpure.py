import json
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
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

        all_results = [extractors.extract_info_from_search(first_app)]

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

    def get_info(self, name: str) -> dict:
        top_app = self.search_top(name)
        first_app_from_search : dict = json.loads(top_app)
        # This variable already give us the needed information about the package
        # So dl_btn = divs.find("a", class_="download_apk_news").attrs is not necessary anymore

        # The download page has more information about the package
        info_url =  str(first_app_from_search.get('package_url')) + '/download'
        html_obj = self.__helper(info_url)

        return json.dumps(extractors.extract_info_from_get_info(html_obj) | first_app_from_search, indent=4)
        
    
    def download(self, name: str, version: str = None, XAPK: bool = False) -> str | None:
        
        app_type = 'XAPK' if XAPK else 'APK'
        
        version_code = None
        if version:
            versions = json.loads(self.get_versions(name))
            for version_ in versions:
                if str(version_.get('version')) == version:
                    version_code = version_.get("version_code")
                    break
        
        version_code = version_code or package_info.get('package_version_code')
        
        package_info : dict = json.loads(self.get_info(name))
        base_url = f'https://d.apkpure.com/b/{app_type}/' \
                + package_info.get('package_name') \
                + '?versionCode=' \
                + version_code

        return self.__downloader(base_url, name, version_code=version_code)

    def __downloader(self, url: str, name : str = None, version_code : str = None) -> str | None:
        response = self.__get_response(url=url, stream=True)
        file_size = int(response.headers.get('Content-Length', 0))
        
        filename = response.headers.get('Content-Disposition').split('filename=')[1].replace('"', '')
        with open(f'{version_code}_{filename}', 'wb') as package_file:
            progress_bar = tqdm(total=file_size, unit='B', unit_scale=True, desc=f'Downloading {name}',dynamic_ncols=True, leave=True)
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    package_file.write(chunk)
                    progress_bar.update(len(chunk))
            progress_bar.close()
            
        return f'{name} was downloaded' if response else f'Error while trying to download {url}'