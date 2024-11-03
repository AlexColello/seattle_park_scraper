import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import csv

LIST_NAME = "test"

BATCH_WAIT_TIME = 90

driver = uc.Chrome()
driver.get("http://maps.google.com/")

# Wait for the site to load enough to have a sign in button.
time.sleep(1)

driver.find_element(By.CSS_SELECTOR, "[aria-label='Sign in']").click()
input("Press the ENTER key when you are done signing in.")


def parse_list_name(list_name_element):
    return list_name_element.text.split("\n")[-1]


with open("google_maps_links.txt", "r") as f:
    list_index = None
    count = 0
    for link, name in csv.reader(f):
        try:
            print(f"Adding {name} at {link}")

            driver.get(link)
            time.sleep(3)

            driver.find_element(By.CSS_SELECTOR, "[aria-label*='Save']").click()
            time.sleep(0.75)

            selector = driver.find_element(
                By.CSS_SELECTOR, "[aria-label='Save in your lists']"
            )
            if list_index is None:
                location_lists = selector.find_elements(
                    By.CSS_SELECTOR, "[role='menuitemradio']"
                )
                for i, location_list in enumerate(location_lists):
                    if parse_list_name(location_list) == LIST_NAME:
                        list_index = i

                if list_index is None:
                    print(
                        f"Failed to find '{LIST_NAME}' in the available lists: {[parse_list_name(x) for x in location_lists]}"
                    )
                    exit(1)

            list_element = selector.find_element(
                By.CSS_SELECTOR, f"[data-index='{list_index}']"
            )
            if list_element.get_attribute("aria-checked") == "true":
                print(f"{name} is already in {LIST_NAME}")
                continue

            list_element.click()
            count += 1
            # Seems like it maxes out at 60 at a time, going a little lower to be safe.
            if count % 55 == 0:
                print(f"Waiting {BATCH_WAIT_TIME} seconds for rate limiting to reset")
                time.sleep(BATCH_WAIT_TIME)
        except:
            input(
                "Something went wrong!! Please try to correct the error then press ENTER to continue."
            )

print(f"Finished adding {count} locations to {LIST_NAME}!")
