from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import sys
from datetime import datetime
import json
from selenium.webdriver.common.keys import Keys
from unidecode import unidecode
import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains
import requests
from bs4 import BeautifulSoup
from collections import defaultdict


now = datetime.now()
year, month, day = now.year, now.month, now.day

reviews = []

album_review_urls = set()

BASE_PAGE = "https://www.theguardian.com/music+tone/albumreview"
WAIT_TIME = 60
driver = webdriver.Chrome('webdriver/chromedriver')

driver.get(BASE_PAGE)

def collect_review_urls():
    # assuming we're on the right page
    this_page_urls = set()
    for a in driver.find_elements_by_xpath("//a[@data-link-name='article']"):
        this_page_urls.add(a.get_attribute("href"))
    #print("found {} album review links on this page".format(len(this_page_urls)))

    return this_page_urls

# once on the base page, go find the pagination list at the bottom and
# specifically the last available page button

last_page  = int(driver.find_element_by_class_name("pagination__action--last ").get_attribute("data-page"))
print("last available page is {}".format(last_page))
album_review_urls.update(collect_review_urls())

# all pages but the first one have URLs like https://www.theguardian.com/music+tone/albumreview?page=2
for i in range(980, last_page + 1):

    driver.get(BASE_PAGE + "/?page=" + str(i))

    print("now on {}".format(driver.current_url))

    # wait unitl that pagination bar is visible
    if i < last_page:
        WebDriverWait(driver, WAIT_TIME).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "pagination__action--static")))
    else:
        print("now searching the last page.. not waiting for the pagination bar")

    album_review_urls.update(collect_review_urls())

    if (i%10 == 0) or (i == last_page):
        print("links collected so far: {}".format(len(album_review_urls)))


driver.quit()

# not time to visit each link
for rl in album_review_urls:

    GOT_PAGE = False

    while not GOT_PAGE:

        try:
            soup = BeautifulSoup(requests.get(rl, timeout=30).content, "lxml")
            GOT_PAGE = True
        except:
            print("requests couldn\'t get a page, retrying...")
            time.sleep(3)

    this_review = defaultdict()

    try:
        this_review["review_title"] = unidecode(soup.find(class_="content__headline")).text.strip().lower()
    except:
        this_review["review_title"] = None
    try:
        # d = soup.find("div", class_="stars", role = "presentation")
        # print("div class stars", d)
        # print(d.find_all("span"))
        this_review["theguardian_score"] = str(len(soup.find("div", class_="stars", role = "presentation").find_all("span", class_= "star__item--golden"))) + "/5"
    except:
        this_review["theguardian_score"] = None
    try:
        this_review["review_text"] = unidecode(soup.find("div", {"itemprop": "reviewBody"}).p.text.lower().strip())
    except:
        this_review["review_text"] = None

    reviews.append(this_review)
    # print(this_review)

print("saving reviews to json...")
json.dump(reviews, open("theguardian_reviews_{:02d}{:02d}{:02d}.json".format(day, month, year), "w"))

