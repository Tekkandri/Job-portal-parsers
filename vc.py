from bs4 import BeautifulSoup
import requests
from time import sleep
import csv
import undetected_chromedriver as uc
import re

from config import REGEXP_LIST, VC_URL_LIST, headers

def get_list_from_file():
    with open("LIST_OF_VACANCIES_REGEXP.txt", "r", encoding="utf-8") as file:
        for line in file:
            if line.find(" ") != -1:
                line = line.split()
                for j in range(len(line)):
                    if len(line[j]) > 6:
                        temp = list(line[j])
                        temp[0] = "\w"
                        temp.pop()
                        temp[-1] = "\w+"
                        line[j] = "".join(temp)
                    else:
                        line[j] += "\w+"
                line = " ".join(line)
            if len(line.strip()) > 3:
                REGEXP_LIST.append(line.strip())

def get_url_list_to_file():
    with open("vc.txt","w", encoding="utf-8") as file:
        for url in VC_URL_LIST:
            file.write(url + "\n")

def get_url_list_from_file():
    with open("vc.txt","r",encoding="utf-8") as file:
        VC_URL_LIST.clear()
        lines = file.readlines()
        for line in lines:
            VC_URL_LIST.append(line.strip())


def main():
    get_url_list_from_file()
    jobs = []
    url = "https://vc.ru/job?area=0"
    driver = uc.Chrome(headless=True)
    driver.get(url)
    SCROLL_PAUSE_TIME = 0.5

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    sleep(3)
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.close()

    vac_urls_list = []

    divs = soup.find_all("div", {"class":"feed__item"})
    for div in divs:
        name = div.find("div",{"class":"content-title"}).text
        vac_url = div.find("a",{"class":"content-link"})["href"]

        for reg in REGEXP_LIST:
            regexp = re.compile(reg)
            if regexp.findall(name):
                if vac_url not in VC_URL_LIST:
                    VC_URL_LIST.append(vac_url)
                    vac_urls_list.append(vac_url)

    for url in vac_urls_list:
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "lxml")
        name = soup.find("h1",{"class":"content-title"}).text
        descr = soup.find("div",{"class":"content"}).find_all("div",{"class":"l-island-a"})[1].text

        jobs.append({
            "name": name.rstrip().lstrip(),
            "description": descr,
            "url": url,
        })

    get_url_list_to_file()
    return jobs



if __name__=="__main__":
    get_list_from_file()
    with open("vc.csv", "w", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="|")
        writer.writerow(["Name", "Url"])
        for job in main():
            writer.writerow([job["name"], job["url"]])