import datetime

import requests
import re
import csv
import pandas as pd
import random
from time import sleep
from fake_useragent import UserAgent

from config import headers, REGEXP_LIST, HH_VAC_LIST, HH_ID_LIST, proxies

headers1 = {'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'}
headers2 = {'accept' : '*/*',
            'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'}


def get_list_of_regexp(filename):
    df = pd.read_excel(filename, dtype=str)
    lst = []

    for i in range(df.shape[0]):

        columnSeriesobj = df.iloc[i, 1:3]
        column_lst = list(columnSeriesobj.values)
        cleaned_lst = [x for x in column_lst if str(x) != "nan"]

        if str(columnSeriesobj.values[-1]) != "nan":
            items = ", ".join(cleaned_lst).split(", ")
            lst.append(items)

    for item in lst:
        if " " in item or "":
            item.remove(" ")

    with open("LIST_OF_VACANCIES.txt","w", encoding="utf-8") as file:
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

def get_list_from_file_hh_ru():
    with open("LIST_OF_VACANCIES_HH_RU.txt","r",encoding="utf-8") as file:
        for line in file:
            vac = line.replace(" ", "+")
            HH_VAC_LIST.append(vac.strip())

def get_id_list_to_file():
    with open("HH_ID_LIST.txt","w", encoding="utf-8") as file:
        for id in HH_ID_LIST:
            file.write(str(id) + "\n")

def get_id_list_from_file():
    with open("HH_ID_LIST.txt","r",encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines:
            HH_ID_LIST.append(line.strip())

def hh_parse():
    get_id_list_from_file()
    jobs = []
    session = requests.Session()
    CUR_DATE = datetime.datetime.now()
    for vac in HH_VAC_LIST:

        ua = UserAgent()
        url = f"https://api.hh.ru/vacancies?text={vac}"
        session.cookies.clear()
        head = {'user-agent': ua.random}
        resp = session.get(url, headers=head, proxies=proxies[random.randrange(0,2)]).json()

        try:
            pages = resp["pages"]
            for page in range(pages):
                sleep(random.randrange(1,3))

                ua = UserAgent()
                url = f"https://api.hh.ru/vacancies?text={vac}&page={page}"
                session.cookies.clear()
                resp = session.get(url, headers={'user-agent':ua.random},proxies=proxies[random.randrange(0,2)]).json()

                for item in resp["items"]:

                    name = item["name"]
                    try:
                        responsibility = item["snippet"]["responsibility"].replace("<highlighttext>","").replace("</highlighttext>","")
                    except:
                        responsibility = ""
                    try:
                        requirement = item["snippet"]["requirement"].replace("<highlighttext>", "").replace("</highlighttext>", "")
                    except:
                        requirement = ""
                    descr = responsibility+requirement
                    id = item["id"]
                    vac_url = "https://hh.ru/vacancy/"+str(id)

                    full_date = item["published_at"]
                    format = "%Y-%m-%d"
                    date = datetime.datetime.strptime(full_date.split("T")[0], format)
                    DD = datetime.timedelta(days=30)

                    for reg in REGEXP_LIST:
                        regexp = re.compile(reg)
                        if regexp.findall(name):
                            if item["salary"] != None:
                                cur = item["salary"]["currency"]
                                count = item["salary"]["from"]
                                if count != None:
                                    if (cur == "RUR" and count>100000) or ((cur == "USD" or cur == "EUR") and count > 1000):
                                        if id not in HH_ID_LIST:
                                            if date > (CUR_DATE-DD):
                                                HH_ID_LIST.append(id)
                                                jobs.append({
                                            "name": name,
                                            "description": descr,
                                            "url": vac_url,
                                            "salary": f"{count} {cur}"
                                            })
                            else:
                                if id not in HH_ID_LIST:
                                    if date > (CUR_DATE-DD):
                                        HH_ID_LIST.append(id)
                                        jobs.append({
                                    "name": name,
                                    "description": descr,
                                    "url": vac_url,
                                    "salary": "Не указана"
                                    })
        except:
            print("Captcha")
            # resp = session.get(resp["errors"][0]["captcha_url"]+"&backurl="+url, headers=head)
    get_id_list_to_file()
    res_list = [i for n, i in enumerate(jobs)
                if i not in jobs[n + 1:]]
    return res_list

if __name__ == "__main__":
    get_list_of_regexp("CRC-подписка_telegram_2023-07-25.xlsx")
    get_list_of_vac_hh_ru("CRC-подписка_telegram_2023-07-25.xlsx")
    get_list_from_file()
    get_list_from_file_hh_ru()
    with open("hhru.csv", "w", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="|")
        writer.writerow(["Name", "Url", "Salary"])
        for job in hh_parse():
            writer.writerow([job["name"], job["url"], job["salary"]])