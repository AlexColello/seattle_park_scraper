# The goal of this program is to scrape the locations of all of the parks in Seattle from this link:
# https://seattle.gov/parks/allparks

from bs4 import BeautifulSoup
import requests
import re
from pprint import pprint
import csv

missing_map_link = []


def get_maps_link_from_page(id):
    url = f"https://seattle.gov/parks/allparks/?ID={id}"
    r = requests.get(url)
    soup = BeautifulSoup(r.content, features="html.parser")

    if len(soup.find_all("script")) == 1:
        return None

    if soup.find(string="The park page has moved"):
        redirect_name = soup.a["href"]
        url = f"https://seattle.gov/parks/allparks/{redirect_name}"
        r = requests.get(url)
        soup = BeautifulSoup(r.content, features="html.parser")

    # print(soup)

    link = soup.find(href=re.compile(r"https:\/\/goo\.gl\/."))

    if link is None:
        print("Could not find a Google Maps link on the page!")
        missing_map_link.append(url)
        return None

    return link["href"]


def main():
    with open("data_url.txt", "r") as f:
        data_url = f.read()

    all_data = requests.get(data_url).json()
    parks = all_data["features"]
    print(f"Found {len(parks)} parks in the list")

    successful_pages = 0
    with open("google_maps_links.txt", "w") as f:
        map_link_writer = csv.writer(f)
        for park in parks:
            park_name = park["attributes"]["PMA_Name"]
            park_id = park["attributes"]["PMA"]
            print(
                "--------------------------------------------------------------------"
            )
            print(f"Trying {park_name}, {park_id}")
            try:
                map_link = get_maps_link_from_page(park_id)
            except Exception as e:
                print(f"Failed to parse {park_name}, {park_id}")
                raise e

            if map_link is None:
                print(f"Failed to find valid page for {park_name}")
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
