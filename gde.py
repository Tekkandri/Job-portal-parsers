import requests
from requests import adapters
from bs4 import BeautifulSoup
import re
from time import sleep
import csv
import random
import datetime

from config import REGEXP_LIST, GDE_ID_LIST, GDE_VAC_LIST, headers

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

def get_list_from_file_gde():
    with open("LIST_OF_VACANCIES_REQUEST.txt", "r", encoding="utf-8") as file:
        GDE_VAC_LIST.clear()
        for line in file:
            vac = line.replace(" ", "+")
            GDE_VAC_LIST.append(vac.strip())

def get_id_list_to_file():
    with open("gde.txt","w", encoding="utf-8") as file:
        for id in GDE_ID_LIST:
            file.write(str(id) + "\n")

def get_id_list_from_file():
    with open("gde.txt","r",encoding="utf-8") as file:
        GDE_ID_LIST.clear()
        lines = file.readlines()
        for line in lines:
            GDE_ID_LIST.append(line.strip())

def main():
    get_id_list_from_file()
    jobs = []
    session = requests.session()
    adapter = requests.adapters.HTTPAdapter(max_retries=20)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    CUR_DATE = datetime.datetime.now()
    for vac in GDE_VAC_LIST:
        url = f"https://gde.ru/rabota?Filter%5Bdistrict_id%5D=&Filter%5Bsearch_string%5D={vac}"
        print(url)
        resp = session.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "lxml")

        try:
            last_page_url = soup.find("ul",{"class":"pagination"}).find_all("li")[-1].find("a")["href"]
            last_page = int(re.findall(r'page=\d+', last_page_url)[0].split("=")[1])
        except:
            last_page = 0
            pass

        for page in range(1, last_page):
            url =f"https://gde.ru/rabota?Filter%5Bdistrict_id%5D=&Filter%5Bsearch_string%5D={vac}&page={page}"
            print(url)
            sleep(random.randrange(1,3))
            resp = session.get(url, headers=headers)
            soup = BeautifulSoup(resp.text, "lxml")

            divs = soup.find("ul",{"class":"product-list"}).find_all("div",{"class":"top-info"})

            for div in divs:
                name = div.find("div", {"class": "title"}).find("a").text
                vac_url = div.find("div", {"class": "title"}).find("a")["href"]
                desc = div.find("div", {"class": "description"}).text
                salary_lst = re.findall(r'\d+',div.find("div",{"class":"price"}).text.replace(" ",""))
                salary = 0
                if len(salary_lst) != 0:
                    salary = int(salary_lst[0])

                format = "%Y-%m-%d"
                date = 0
                if div.find("div",{"class":"bottom-panel"}).find("time"):
                    date = datetime.datetime.strptime(div.find("div",{"class":"bottom-panel"}).find("time")["datetime"], format)

                DD = datetime.timedelta(days=30)


                for reg in REGEXP_LIST:
                    regexp = re.compile(reg)
                    if regexp.findall(name):
                        vac_id = re.findall(r'\d{8}', vac_url)
                        if len(vac_id) != 0 and vac_id[0] not in GDE_ID_LIST:
                            if date != 0 and date > (CUR_DATE-DD):
                                if salary > 50000 or len(salary_lst) == 0:
                                    GDE_ID_LIST.append(vac_id[0])
                                    print(name, salary_lst, salary, date)

                                    jobs.append({
                                        "name": name,
                                        "description": desc,
                                        "url": vac_url,
                                    })

    get_id_list_to_file()
    return jobs

if __name__ == "__main__":
    get_list_from_file()
    get_list_from_file_gde()
    with open("gde.csv", "w", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="|")
        writer.writerow(["Name", "Url", "Desc"])
        for job in main():
            writer.writerow([job["name"], job["url"], job["description"]])