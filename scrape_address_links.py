# The goal of this program is to scrape the locations of all of the parks in Seattle from this link:
# https://seattle.gov/parks/allparks

from bs4 import BeautifulSoup
import requests
import re
from pprint import pprint
import csv
from enum import Enum


class LinkResult(Enum):
    Successful = "successful"
    LinkMissing = "link_missing"
    PageMissing = "page_missing"


# https://www.seattle.gov/parks/allparks/parks-e-h?pageNum=1&itemsPer=1000&displayType=Thumbnail_Excerpt


def get_park_container():
    with open("data_url.txt", "r") as f:
        data_url = f.read()

    all_data = requests.get(data_url).json()
    return all_data["features"]


def get_park_info(raw_park_data):
    park_name = raw_park_data["attributes"]["PMA_Name"]
    park_id = raw_park_data["attributes"]["PMA"]

    sanitized_name = park_name.lower().replace(" ", "-").replace(".", "")
    url = f"http://seattle.gov/parks/allparks/{sanitized_name}"
    return park_name, park_id, url


def get_maps_link_from_page(url: str):
    r = requests.get(url, verify=False)
    if r.status_code != 200:
        print(f"Page returned unsuccessful status code {r.status_code}")
        return None, LinkResult.PageMissing

    soup = BeautifulSoup(r.content, features="html.parser")

    if len(soup.find_all("script")) == 1:
        return None, LinkResult.PageMissing

    if soup.find(string="The park page has moved"):
        redirect_name = soup.a["href"]
        url = f"https://seattle.gov/parks/allparks/{redirect_name}"
        r = requests.get(url, verify=False)
        soup = BeautifulSoup(r.content, features="html.parser")

    # print(soup)

    link = soup.find(href=re.compile(r"https:\/\/goo\.gl\/."))

    if link is None:
        print("Could not find a Google Maps link on the page!")
        return None, LinkResult.LinkMissing

    return link["href"], LinkResult.Successful


def main():

    parks = get_park_container()
    print(f"Found {len(parks)} parks in the list")

    successful_pages = 0
    missing_map_link = []
    with open("google_maps_links.txt", "w", newline="", encoding="utf-8") as f:
        map_link_writer = csv.writer(f)
        for park in parks:
            park_name, park_id, url = get_park_info(park)
            print(
                "--------------------------------------------------------------------"
            )
            print(f"Trying {park_name}, {park_id}")
            try:
                map_link, result = get_maps_link_from_page(url)
            except Exception as e:
                print(f"Failed to parse {park_name}, {park_id}")
                raise e

            if map_link is None:
                print(f"Failed to find valid page for {park_name}")
                if result == LinkResult.LinkMissing:
                    missing_map_link.append(url)
                continue

            print(f"Map link for {park_name}: {map_link}")
            map_link_writer.writerow([map_link, park_name])
            successful_pages += 1

    print("Valid pages with no maps:")
    pprint(missing_map_link)
    with open("pages_missing_maps.txt", "w") as f:
        for page in missing_map_link:
            f.write(f"{page}\n")

    print(
        f"Successfully found {successful_pages} links and {len(missing_map_link)} parks with no map link for at total of {successful_pages + len(missing_map_link)} parks"
    )


if __name__ == "__main__":
    main()
