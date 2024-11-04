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

    alternative_url = f"https://seattle.gov/parks/allparks/?ID={park_id}"
    sanitized_name = park_name.lower().replace(" ", "-").replace(".", "")
    url = f"https://seattle.gov/parks/allparks/{sanitized_name}"
    return park_name, park_id, url, alternative_url

def get_listed_parks():
    links = []
    for start_letter, end_letter in [('a', 'd'), ('e', 'h'), ('i', 'l'), ('m', 'p'), ('q', 't'), ('u', 'z')]:
        r = requests.get(f"https://www.seattle.gov/parks/allparks/parks-{start_letter}-{end_letter}?pageNum=1&itemsPer=1000", verify=False)
        assert r.status_code == 200

        soup = BeautifulSoup(r.content, features="html.parser")
        rows = soup.find_all("h2", {"class": "paginationTitle"})
        for row in rows:
            name = row.text.strip()
            url = f'https://seattle.gov/{row.a["href"]}'
            links.append((name, url))
    return links

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

    link = soup.find(href=re.compile(r"(https:\/\/goo\.gl\/.)|(https:\/\/www.google.com\/maps\/place\/.)"))

    if link is None:
        print("Could not find a Google Maps link on the page!")
        return url, LinkResult.LinkMissing

    return link["href"], LinkResult.Successful


def main():

    successful_pages = []
    successful_links = set()
    missing_map_link = set()

    def record_results(result, map_link, park_name):
        if result == LinkResult.Successful:
            print(f"Map link for {park_name}: {map_link}")
            if map_link in successful_links:
                print(f"A page with a link to {map_link} already exists! Skipping {park_name}")
            else:
                successful_links.add(map_link)
                successful_pages.append((park_name, map_link))
        elif result == LinkResult.PageMissing:
            print(f"Failed to find valid page for {park_name}")
        elif result == LinkResult.LinkMissing:
            print(f"Map link was missing from the page for {park_name}")
            missing_map_link.add(map_link)

    listed_parks = get_listed_parks()
    print(f"Found {len(listed_parks)} listed parks")
    for park_name, url in listed_parks:
        print("--------------------------------------------------------------------")
        print(f"Trying {park_name}")
        try:
            map_link, result = get_maps_link_from_page(url)
            record_results(result, map_link, park_name)
        except Exception as e:
            print(f"Failed to parse {park_name}")
            raise e

    parks = get_park_container()
    print(f"Found {len(parks)} parks from GIS")

    for park in parks:
        park_name, park_id, url, alt_url = get_park_info(park)
        print("--------------------------------------------------------------------")
        print(f"Trying {park_name}, {park_id}")
        try:
            map_link, result = get_maps_link_from_page(url)
            record_results(result, map_link, park_name)
            if alt_url is not None:
                map_link, result = get_maps_link_from_page(alt_url)
                record_results(result, map_link, park_name)
        except Exception as e:
            print(f"Failed to parse {park_name}, {park_id}")
            raise e

    successful_pages = successful_pages
    missing_map_link = list(missing_map_link)

    successful_pages.sort()
    missing_map_link.sort()

    with open("google_maps_links.txt", "w", newline="", encoding="utf-8") as f:
        map_link_writer = csv.writer(f)
        for park_name, map_link in successful_pages:
            map_link_writer.writerow([park_name, map_link])

    print("Valid pages with no maps:")
    pprint(missing_map_link)
    with open("pages_missing_maps.txt", "w") as f:
        for page in missing_map_link:
            f.write(f"{page}\n")

    print(
        f"Successfully found {len(successful_pages)} links and {len(missing_map_link)} parks with no map link for a total of {len(successful_pages) + len(missing_map_link)} parks"
    )


if __name__ == "__main__":
    main()
