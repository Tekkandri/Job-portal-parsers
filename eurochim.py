import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

from config import headers, REGEXP_LIST

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

    eurochim_url = "https://www.eurochem.ru/vacancies/page/1/"

    resp = requests.get(eurochim_url, headers=headers)

    soup = BeautifulSoup(resp.text, "lxml")

    last_page = soup.find("div",{"class":"pagging"}).findAll("a",{"class":"page-numbers"})

    vacancies_urls = []
    list_of_vacancies = []

    for page in range(1,int(last_page[-1].text)+1):
        url = f"https://www.eurochem.ru/vacancies/page/{page}/"
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "lxml")

        vacancies = soup.find("ul",{"class":"col-list"}).findAll("a")

        for vac in vacancies:
            name = vac.find("b",{"class":"title"}).text
            url = vac["href"]

            for reg in REGEXP_LIST:
                regexp = re.compile(reg)
                if regexp.findall(name):
                    vacancies_urls.append(url)

    for url in vacancies_urls:

        resp = requests.get(url, headers=headers)

        soup = BeautifulSoup(resp.text, "lxml")

        name = soup.find("h1").text
        text = soup.find("div",{"class":"content__box"}).text
        txt = ""
        print(name, url)

        for line in text.splitlines():
            if len(line) != 0 and line != " ":
                line.strip("\n")
                line = line.replace("\xa0", "")
                txt += line + "\n"

        list_of_vacancies.append({
            "name": name,
            "description": txt,
            "url": url
        })

    return list_of_vacancies

if __name__ == "__main__":
    get_list_from_file()
    for item in main():
        print(item["name"])