import json
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import sys
import cloudscraper


# Utils
from . import extractors as scraper

class ApkPure:
    def __init__(self) -> None:
        self.query_url = "https://apkpure.com/search?q="

    def __check_name(self, name : str) -> None :
        """Verify if the query is valid to avoid errors
        
        Keyword arguments:
        name : the query
        Return: None | exit
        """
        
        name = name.strip()
        name.replace(":", " ")
        if not name:
            sys.exit(
                "No search query provided!",
            )

    def __soup_factory(self, url) -> BeautifulSoup:
        """Returns soup object from an given URL,
        using cloudscraper to avoid cloudflare anti-bot protection
        
        Keyword arguments:
        url : the website URL
        Return: BeautifulSoup
        """
        
        response = self.__get_response(url=url)
        if not response:
            sys.exit("Error: Bad request!")
        return BeautifulSoup(response.text, "html.parser")

    def __get_response(self, url: str, **kwargs) -> requests.Response | None:
        """A wrapper for requests.get to avoid cloudflare anti-bot protection
        this function accept any argument for requests.get, like stream, timeout, etc.
        Also, it dont need header, by default the cloudscraper already set the header.
        
        Keyword arguments:
        url : the target url
        kwargs : additional arguments for requests.get
        example:
        __get_response("https://google.com", timeout = 10)
        Return: resquest.Response | None
        """

        scraper = cloudscraper.create_scraper()
        response = scraper.get(url=url, **kwargs)
        
        if response.status_code == 403:
            sys.exit("Error: Request was blocked, try to update the ApkPure API!")

        return response if response.status_code == 200 else None

    

    def get_first_app_result(self, name: str) -> str | Exception:
        
        """Get first app result from the search result page in ApkPure.
        Is harder to get app not found, because the search result is dynamic.
        To avoid the app not found, use the check_name method.
        
        Keyword arguments:
        name : the query
        Return: JSON string or Exception
        """
        self.__check_name(name)

        query_url = self.query_url + name
        soup_obj = self.__soup_factory(query_url)

        first_div: BeautifulSoup = soup_obj.find("div", class_="first")
        
        package_url = first_div.find("a", class_="first-info")

        if first_div is None:
            raise LookupError("App not found")

        if package_url is None:
            package_url = first_div.find("a", class_="dd")

        result = scraper.extract_info_from_search(first_div)

        return json.dumps(result, indent=4)
    
    def get_top_app(self, name):
        """A wrapper for the get first app result method.
        """
        
        return self.get_first_app_result(name)
    
    def get_all_apps_results(self, name: str) -> list[dict]:
        """Get all app results from the search result page in ApkPure.
        
        Keyword arguments:
        name : the query
        Return: JSON string or Exception
        """
        
        self.__check_name(name)

        url = self.query_url + name
        soup = self.__soup_factory(url)

        first_app = soup.find("div", class_="first")

        list_of_apps = soup.find("ul", id="search-res")  # UL
        apps_in_list_of_apps = list_of_apps.find_all("li")  # LI's

        all_results = [scraper.extract_info_from_search(first_app)] # add the first result from search to the all results

        all_results.extend(
            scraper.extract_info_from_search(app)
            for app in apps_in_list_of_apps
        )
        
        return json.dumps(all_results, indent=4)

    def get_versions(self, name) -> str:
        """Get all versions of the query app.
        The app is the first result from the query, so check if get_first_app_result is
        giving you what app that you want.
        
        Keyword arguments:
        name : the query
        Return: an JSON array of versions or Exception
        """
        
        self.__check_name(name)
        first_app_from_search : dict = json.loads(self.get_first_app_result(name))
        
        version_url = str(first_app_from_search.get('package_url')) + "/versions"
        
        soup = self.__soup_factory(version_url)
    
        versions_list : list = soup.find("ul", class_="ver-wrap")

        items : list[BeautifulSoup] = versions_list.find_all("li")
        items.pop() # Delete the last one item, cause its a bottom link
        
        all_versions : list[dict]= []
        
        all_versions = [
            scraper.extract_info_from_versions(item.find("a", class_="ver_download_link" ))
            for item in items
        ]
        
        # for item in items:
        #     data : BeautifulSoup = item.find("a", class_="ver_download_link") # tag a
            
        #     all_versions.append(
        #         scraper.extract_info_from_versions(data)
        #     )
            
        return json.dumps(all_versions, indent=4)

    def get_info(self, name: str) -> dict:
        """Get all information about the query app.
        The app is the first result from the query, so check if get_first_app_result is
        giving you what app that you want.
        
        informations:
        - title
        - developer
        - rating
        - donwload count
        - lastest update
        - lastest version
        - file extension (APK or XAPK)
        - icon url
        - package extension (apk, xapk... just work in search all, by default use the file extension property)
        - package name (com.android.example)
        - package size (in Bytes)
        - package version (example 1.0.2)
        - package version code (internal code for one version in apk pure)
        - download link 
        - package url        
        
        Keyword arguments:
        name : the query
        Return: JSON string or Exception
        """
        
        self.__check_name(name)
        top_app = self.get_first_app_result(name)
        first_app_from_search : dict = json.loads(top_app) # This variable already give us the needed information about the package
        # So dl_btn = divs.find("a", class_="download_apk_news").attrs is not necessary anymore

        info_url =  str(first_app_from_search.get('package_url')) + '/download'
        html_obj = self.__soup_factory(info_url)

        return json.dumps(
            scraper.extract_info_from_get_info(html_obj) | first_app_from_search,
            indent=4
            )
        
    
    def download(self, name: str, version: str = None, XAPK: bool = False) -> str | None:
        """Download an apk or xapk.
        the downloaded app is the first result from the get_first_app_result() method, so check it before.
        
        Keyword arguments:
        name : the query
        version : the version of the app, if not specified it will be the lastest version on site
        XAPK : specify True to download an xapk, False by default
        Return: None
        """
        
        self.__check_name(name)
        
        app_type = 'XAPK' if XAPK else 'APK'
        
        package_info : dict = json.loads(self.get_info(name))
        
        version_code = None
        if version:
            versions = json.loads(self.get_versions(name))
            for version_ in versions:
                if str(version_.get('version')) == version:
                    version_code = version_.get("version_code")
                    break
        
        version_code = version_code or package_info.get('package_version_code')
        
        base_url = f'https://d.apkpure.com/b/{app_type}/' \
                + package_info.get('package_name') \
                + '?versionCode=' \
                + version_code

        return self.__downloader(url=base_url, name=name, version_code=version_code)

    def __downloader(self, url: str, name : str = None, version_code : str = None) -> str | None:
        """The downlaoder method, dont use separetaly.
        """
        
        response = self.__get_response(url=url, stream=True)
        file_size = int(response.headers.get('Content-Length', 0))
        
        # handle the name of filename
        filename = response.headers.get('Content-Disposition').split('filename=')[1].replace('"', '').replace(" ", '').replace(';', '').replace(':', '')
        
        with open(f'{filename}', 'wb') as package_file:
            progress_bar = tqdm(total=file_size, unit='B', unit_scale=True, desc=f'Downloading {name}',dynamic_ncols=True, leave=True)
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    package_file.write(chunk)
                    progress_bar.update(len(chunk))
            progress_bar.close()
            
        return f'{name} was downloaded' if response else f'Error while trying to download {url}'