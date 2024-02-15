import requests
from bs4 import BeautifulSoup
import re
import csv

from config import REGEXP_LIST, VENTRA_URL_LIST, headers

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
    with open("ventra.txt","w", encoding="utf-8") as file:
        for url in VENTRA_URL_LIST:
            file.write(url + "\n")

def get_url_list_from_file():
    with open("ventra.txt","r",encoding="utf-8") as file:
        VENTRA_URL_LIST.clear()
        lines = file.readlines()
        for line in lines:
            VENTRA_URL_LIST.append(line.strip())

def main():
    get_url_list_from_file()
    url = "https://ventra.ru/career/vacancies/?PAGEN_1=1"
    session = requests.session()
    resp = session.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "lxml")
    jobs = []

    pages = soup.find("div", {"class":"pages"}).find_all("a",{"class":"pages__item"})[-2]

    for i in range(1,int(pages.text)):
        url = f"https://ventra.ru/career/vacancies/?PAGEN_1={i}"
        resp = session.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "lxml")
        divs = soup.find_all("div",{"class":"b-vacancy-teaser"})

        for div in divs:
            name = div.find("div",{"class":"b-vacancy-teaser__title"}).text
            descr = div.find("div",{"class":"b-vacancy-teaser__text"}).text
            vac_url = div.find("div",{"class":"b-vacancy-teaser__button"}).find("a")["href"]

            for reg in REGEXP_LIST:
                regexp = re.compile(reg)
                if regexp.findall(name):
                    if vac_url not in VENTRA_URL_LIST:
                        VENTRA_URL_LIST.append(vac_url)
                        print(name, descr)

                        jobs.append({
                            "name": name.rstrip().lstrip(),
                            "description": descr,
                            "url": vac_url
                        })
    get_url_list_to_file()
    return jobs



if __name__ == "__main__":
    get_list_from_file()
    with open("ventra.csv", "w", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="|")
        writer.writerow(["Name", "Url"])
        for job in main():
            writer.writerow([job["name"], job["url"]])