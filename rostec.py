import requests
from bs4 import BeautifulSoup
import re


from config import REGEXP_LIST, headers

def main():

    rostec_url = "https://rostec.ru/careers/vacancy/"

    start_url =  "https://rostec.ru"

    vacancies_urls = []
    list_of_vacancies = []

    resp = requests.get(rostec_url, headers=headers)

    soup = BeautifulSoup(resp.text, "lxml")

    vacancies = soup.findAll("div",{"class":"middle-news"})

    for vacancy in vacancies:

        name = vacancy.find("h2").find("a").text

        for reg in REGEXP_LIST:
            regexp = re.compile(reg)
            if regexp.findall(name):
                vacancies_urls.append(start_url+vacancy.find("h2").find("a")["href"])

    for url in vacancies_urls:
        resp = requests.get(url, headers=headers)


        soup = BeautifulSoup(resp.text, "lxml")
        name = soup.find("div", {"class":"person"}).find("h1").text
        text = soup.find("div", {"class":"person"}).find("div",{"id":"block2"}).text
        txt = ""
        for line in text.splitlines():
            if len(line) != 0 and line != " ":
                txt += line + "\n"

        list_of_vacancies.append({
            "name": name,
            "description": txt,
            "url": url
        })

    return  list_of_vacancies