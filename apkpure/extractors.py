from bs4 import BeautifulSoup
import html
def extract_info_from_search(html_element):
        def get_basic_info() -> dict:
            title = html_element.find("p", class_="p1")
            developer = html_element.find("p", class_="p2")
            return {
                "title": title.text.strip() if title else "Unknown",
                "developer": developer.text.strip() if developer else "Unknown",
            }

        def get_package_url(html_element) -> dict:
            package_url = html_element.find("a", class_="first-info")

            if package_url is None:
                package_url = html_element.find("a", class_="dd")

            return {"package_url": package_url.attrs.get("href", "Unknown")}

        def get_icon() -> dict:
            icon = html_element.find("img")

            return {"icon": icon.attrs.get("src", "Unknown") if icon else "Unknown"}

        def get_package_data() -> dict:
            package_data = html_element.attrs
            
            if not package_data.get('class', ''):
                package_data = html_element.find("a", class_="is-download")
                
            package_extension = package_data.get("data-dt-apk-type", 'Uknown or Just for Search All')
            package_name = package_data.get("data-dt-app", 'Uknown')
            package_size = package_data.get("data-dt-filesize", 'Uknown')
            package_version = package_data.get("data-dt-version", 'Uknown')
            package_version_code = package_data.get("data-dt-versioncode", 'Uknown')

            return {
                "package_extension" : package_extension,
                "package_name" : package_name,
                "package_size" : package_size,
                "package_version" : package_version,
                "package_version_code" : package_version_code
            }

        def get_download_link() -> dict:
            if download_link := html_element.find("a", class_="is-download"):
                return {"download_link": download_link.attrs.get("href", "Unknown")}

            download_link = html_element.find("a", class_="da")

            return {"download_link": download_link.attrs.get("href", "Unknown")}

        basic_info: dict = get_basic_info()
        package_url: dict = get_package_url(html_element)
        icon: dict = get_icon()
        package_data: dict = get_package_data()
        download_link: dict = get_download_link()

        # Spread all the info into the all_info and then dump it to json
        app_info = basic_info | icon | package_data | download_link | package_url

        return app_info
    
def extract_info_from_versions(html_element : BeautifulSoup):
    def get_package_info(html_element : BeautifulSoup) -> dict:
            classes : dict = html_element.attrs
            
            package_version = classes.get("data-dt-version", 'Unknown')
            package_size = classes.get("data-dt-filesize", "Unknown")
            package_version_code = classes.get("data-dt-versioncode", "Unknown")
            
            return {
                    "version": package_version,
                    "size": package_size,
                    "version_code": package_version_code,
                }
            
    def get_update_on(html_element : BeautifulSoup) -> dict:
        update_on = html_element.find("span", class_="update-on").text
        
        return {
            "update_on": update_on
        }
        
    package_info = get_package_info(html_element)
    package_update_on = get_update_on(html_element)
    
    all_info = package_info | package_update_on
    
    return all_info

def extract_info_from_get_info(html_element : BeautifulSoup) -> dict :
    head_banner : BeautifulSoup  = html_element.find("div", class_="info-content")

    # <h1 class="info-title">Example</h1>
    title = head_banner.find("h1", class_="info-title").get_text(strip=True)
    
    
    # Lastest version need one more step also as the developer info
    """
    <span class="info-sdk"> 
        <span>3.6.2.18580071</span>
        by Activision Publishing, Inc.
    </span>
    """
    developer = head_banner.find("span", class_="info-sdk").contents[-1].replace("by ", '').strip()
    
    version = head_banner.find('span', class_=("info-sdk")).span.get_text(strip=True)
    
    
    rating_stars = head_banner.find("span", class_="stars").get_text(strip=True)
    
    # text = &#x202A;4M+, use html unscape to convert to unicode
    download_count = head_banner.find("span", class_="download-count").get_text().removeprefix('\u202a')
    
    last_update = head_banner.find("span", class_="date").get_text(strip=True)
    
    file_extension = head_banner.find("a", class_="info-tag").get_text(strip=True)
    
    
    
    return {
            'title': title,
            'developer': developer,
            'rating': rating_stars,
            'download_count': download_count,
            'last_update': last_update,
            'latest_version': version,
            "file_extension": file_extension,
        }