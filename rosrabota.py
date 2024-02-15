import requests
from requests import  adapters
from bs4 import BeautifulSoup
import re
import csv
import datetime

from config import REGEXP_LIST, ROSRABOTA_ID_LIST, ROSRABOTA_VAC_LIST, headers

REGIONS = [
    "https://msk.rosrabota.ru/",
    "https://spb.rosrabota.ru/",
    "https://rosrabota.ru/",
    "https://nsk.rosrabota.ru/",
    "https://irk.rosrabota.ru/",
    "https://kras.rosrabota.ru/",
    "https://omsk.rosrabota.ru/",
    "https://nn.rosrabota.ru/",
    "https://rnd.rosrabota.ru/",
    "https://ekat.rosrabota.ru/",
    "https://sam.rosrabota.ru/",
    "https://ufa.rosrabota.ru/"
]


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
        print(REGEXP_LIST)

def get_list_from_file_rosrabota():
    with open("LIST_OF_VACANCIES_REQUEST.txt", "r", encoding="utf-8") as file:
        for line in file:
            vac = line.replace(" ", "+")
            ROSRABOTA_VAC_LIST.append(vac.strip())

def get_id_list_to_file():
    with open("rosrabota.txt","w", encoding="utf-8") as file:
        for id in ROSRABOTA_ID_LIST:
            file.write(str(id) + "\n")

def get_id_list_from_file():
    with open("rosrabota.txt","r",encoding="utf-8") as file:
        ROSRABOTA_ID_LIST.clear()
        lines = file.readlines()
        for line in lines:
            ROSRABOTA_ID_LIST.append(line.strip())

def main():
    get_list_from_file()
    get_id_list_from_file()
    get_list_from_file_rosrabota()
    jobs = []
    session = requests.session()
    adapter = requests.adapters.HTTPAdapter(max_retries=20)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    CUR_DATE = datetime.datetime.now()
    for region in REGIONS:
        for vac in ROSRABOTA_VAC_LIST:
            url = f"{region}vac?text={vac}&salary=3"
            while True:
                session.cookies.clear_session_cookies()
                resp = session.get(url, headers=headers)
                soup = BeautifulSoup(resp.text, "lxml")
                divs = soup.find_all("section",{"data-test":"vacancies-list-item"})

                for div in divs:
                    name = div.find("h3").find("a").text
                    vac_url = "https:"+div.find("h3").find("a")["href"]
                    descr = div.find("div",{"itemprop":"description"}).text.replace("<highlighttext>","").replace("</highlighttext>","")

                    format = "%Y-%m-%d"
                    full_date = div.find("meta",{"itemprop":"datePosted"})["content"]
                    date = datetime.datetime.strptime(full_date.split("T")[0], format)
                    DD = datetime.timedelta(days=30)

                    for reg in REGEXP_LIST:
                        regexp = re.compile(reg)
                        if regexp.findall(name):
                            vac_id = re.findall(r'\d{8}', vac_url)
                            if len(vac_id) != 0 and vac_id[0] not in ROSRABOTA_ID_LIST:
                                if date > (CUR_DATE-DD):
                                    print(name, date)
                                    ROSRABOTA_ID_LIST.append(vac_id[0])

                                    jobs.append({
                                    "name": name,
                                    "description": descr,
                                    "url": vac_url,
                                    })

                try:
                    url ="https:"+soup.find("div",{"class":"pager"}).find("a",{"class":"pager-forward"})["href"]
                except:
                    break
    get_id_list_to_file()
    return jobs

if __name__ == "__main__":
    with open("rosrabota.csv", "w", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="|")
        writer.writerow(["Name", "Url", "Desc"])
        for job in main():
            writer.writerow([job["name"], job["url"], job["description"]])