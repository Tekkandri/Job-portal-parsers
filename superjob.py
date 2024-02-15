import requests
from bs4 import BeautifulSoup as bs
import re
import json
import pandas as pd
import csv
import datetime

from config import headers, REGEXP_LIST, SJ_ID_LIST, SJ_VAC_LIST

def get_list_of_vac_hh_ru(filename):
    df = pd.read_excel(filename, dtype=str)
    lst = []

    for i in range(df.shape[0]):

        columnSeriesobj = df.iloc[i, 1:2]
        column_lst = list(columnSeriesobj.values)
        cleaned_lst = [x for x in column_lst if str(x) != "nan"]

        if str(columnSeriesobj.values[-1]) != "nan":
            items = ", ".join(cleaned_lst).split(", ")
            lst.append(items)

    for item in lst:
        if " " in item:
            item.remove(" ")

    with open("LIST_OF_VACANCIES_HH_RU.txt","w", encoding="utf-8") as file:
        for items in lst:
            for item in items:
                file.write(item + "\n")

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

def get_list_from_file_sj_ru():
    with open("LIST_OF_VACANCIES_HH_RU.txt","r",encoding="utf-8") as file:
        for line in file:
            vac = line.replace(" ", "%20")
            SJ_VAC_LIST.append(vac.strip())

def get_id_list_to_file():
    with open("SJ_ID_LIST.txt","w", encoding="utf-8") as file:
        for id in SJ_ID_LIST:
            file.write(str(id) + "\n")

def get_id_list_from_file():
    with open("SJ_ID_LIST.txt","r",encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines:
            SJ_ID_LIST.append(line.strip())


def sj_parse():
    get_id_list_from_file()
    jobs = []
    session = requests.Session()
    start_url = "https://russia.superjob.ru"
    CUR_DATE = datetime.datetime.now()
    for vac in SJ_VAC_LIST:

        vacancies_urls = []

        base_url = f'https://russia.superjob.ru/vacancy/search/?keywords={vac}'

        resp = session.get(base_url, headers=headers)

        soup = bs(resp.text, "lxml")

        jsons_tag = soup.findAll("script", {"type": "application/ld+json"})

        for tag in jsons_tag:
            jsn = json.loads(tag.text)
            if jsn["@type"] == "ItemList":
                for item in jsn["itemListElement"]:
                    vac_id = re.findall(r'\d{8}', item["url"])
                    if len(vac_id) != 0:
                        if vac_id[0] not in SJ_ID_LIST:
                            SJ_ID_LIST.append(vac_id[0])
                            vacancies_urls.append(item["url"])

        while soup.find("a",{"rel":"next"}):
            try:
                next_page_url = start_url + soup.find("a",{"rel":"next"})["href"]
                print(next_page_url)

                resp = session.get(next_page_url, headers=headers)

                soup = bs(resp.text, "lxml")

                jsons_tag = soup.findAll("script",{"type":"application/ld+json"})

                for tag in jsons_tag:
                    jsn = json.loads(tag.text)
                    if jsn["@type"] == "ItemList":
                        for item in jsn["itemListElement"]:
                            vac_id = re.findall(r'\d{8}', item["url"])
                            if len(vac_id) != 0:
                                if vac_id[0] not in SJ_ID_LIST:
                                    SJ_ID_LIST.append(vac_id[0])
                                    vacancies_urls.append(item["url"])
            except:
                pass

        for url in vacancies_urls:
            try:
                resp = session.get(url, headers=headers)
                soup = bs(resp.text, "lxml")

                jsons = soup.findAll("script", {"type": "application/ld+json"})
                vacancy = json.loads(jsons[1].text)

                name = vacancy["title"]

                format = "%Y-%m-%d"
                date = datetime.datetime.strptime(vacancy["datePosted"].split("T")[0], format)
                DD = datetime.timedelta(days=30)

                count = 0
                print(name, url)

                for reg in REGEXP_LIST:
                    regexp = re.compile(reg)
                    if regexp.findall(name):
                        count+=1
                        text = vacancy["description"].replace("<br>"," ").replace("</br>"," ").replace("<p>"," ").replace("</p>"," ")

                        if count == 1:
                            if vacancy["baseSalary"]:
                                if (vacancy["baseSalary"]["currency"] == "RUB" and vacancy["baseSalary"]["value"]["minValue"] > 50000) or (vacancy["baseSalary"]["currency"] == "USD" and vacancy["baseSalary"]["value"]["minValue"] > 500):
                                    if (date > (CUR_DATE-DD)):
                                        jobs.append({
                                    "name": name,
                                    "description": text,
                                    "url": url
                                    })
                            else:
                                if (date > (CUR_DATE - DD)):
                                    jobs.append({
                                        "name": name,
                                        "description": text,
                                        "url": url
                                    })
            except:
                print("Error url: ", url)
                pass

    get_id_list_to_file()
    return jobs

if __name__ == "__main__":
    get_list_from_file()
    get_list_from_file_sj_ru()
    with open("superjob.csv", "w", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="|")
        writer.writerow(["Name", "Url"])
        for job in sj_parse():
            writer.writerow([job["name"],job["url"]])