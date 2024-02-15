import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

from config import REGEXP_LIST, headers

def get_list_from_file():
    with open("LIST_OF_VACANCIES.txt","r",encoding="utf-8") as file:
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
            REGEXP_LIST.append(line.strip())

def main():

    gazprom_url = "https://www.gazpromvacancy.ru/vacancies/"

    start_url = "https://www.gazpromvacancy.ru/"

    resp = requests.get(gazprom_url,headers=headers)

    soup = BeautifulSoup(resp.text, "lxml")

    last_page = int(soup.find("li",{"class":"last"}).text)
    page = 1

    vacancies_urls = []
    list_of_vacancies = []

    while page <= last_page:

        resp = requests.get(f"https://www.gazpromvacancy.ru/vacancies/page/{page}/",headers=headers)

        soup = BeautifulSoup(resp.text, "lxml")

        vacancies = soup.findAll("div",{"class":"item"})

        for vacancy in vacancies:

            link = vacancy.find("a")["href"]
            name = vacancy.find("div",{"class":"body"}).text

            vacancie_url = start_url+link

            for reg in REGEXP_LIST:
                regexp = re.compile(reg)
                if regexp.findall(name):
                    vacancies_urls.append(vacancie_url)

        page += 1

    for url in vacancies_urls:

        resp = requests.get(url,headers=headers)

        soup = BeautifulSoup(resp.text, "lxml")

        name = soup.find("h1",{"class":"mainHeader"}).text

        vacancy_text = soup.find('div',{"class":"job-requirements"}).text

        list_of_vacancies.append({
            "name": name,
            "description": vacancy_text,
            "url": url
        })

    return list_of_vacancies

if __name__ == "__main__":
    get_list_from_file()
    for item in main():
        print(item["name"], item["url"])