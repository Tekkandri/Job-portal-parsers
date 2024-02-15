import requests
from requests import adapters
from bs4 import BeautifulSoup
import re
import datetime

from config import REGEXP_LIST, headers, RR_ID_LIST, RR_VAC_LIST

rr_regions_urls = []

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

def get_list_from_file_rr_ru():
    with open("LIST_OF_VACANCIES_HH_RU.txt","r",encoding="utf-8") as file:
        for line in file:
            vac = line.replace(" ", "%20")
            RR_VAC_LIST.append(vac.strip())

def get_regions_urls():
    with open("RABOTA_RU_REGION_URLS.txt","r",encoding="utf-8") as file:
        for line in file:
            rr_regions_urls.append(line.strip())

def get_id_list_to_file():
    with open("RR_ID_LIST.txt","w", encoding="utf-8") as file:
        for id in RR_ID_LIST:
            file.write(str(id) + "\n")

def get_id_list_from_file():
    with open("RR_ID_LIST.txt","r",encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines:
            RR_ID_LIST.append(line.strip())

def rr_parse():
    get_id_list_from_file()
    get_regions_urls()
    get_list_from_file()
    get_list_from_file_rr_ru()
    jobs = []
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=20)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    start_url = "https://www.rabota.ru"
    CUR_DATE = datetime.datetime.now()
    for region_url in rr_regions_urls:
        for vac in RR_VAC_LIST:
            base_url = f"{region_url}?query={vac}&sort=relevance"
            urls = []
            resp = session.get(base_url, headers=headers)

            soup = BeautifulSoup(resp.text, "lxml")

            try:
                pages = soup.findAll("a",{"class":"pagination-list__item"})
                last_page = int(pages[-1].text)
                for i in range(1,last_page+1):
                    urls.append(f"{base_url}&page={i}")
            except:
                pass

            for url in urls:
                resp = session.get(url, headers=headers)
                soup = BeautifulSoup(resp.text, "lxml")

                vacancies_divs = soup.findAll("div",{"class":"vacancy-preview-card__top"})

                if len(vacancies_divs) == 0:
                    break

                for div in vacancies_divs:
                    name = div.find("h3",{"class":"vacancy-preview-card__title"}).find("a").text
                    url = start_url + div.find("h3",{"class":"vacancy-preview-card__title"}).find("a")["href"]
                    baseSalarymeta = div.find("meta",{"itemprop":"baseSalary"})
                    baseSalaryspan = div.find("span",{"itemprop":"baseSalary"})

                    format = "%Y-%m-%d"
                    date = datetime.datetime.strptime(div.find("meta",{"itemprop":"datePosted"})["content"].split("T")[0],format)
                    DD = datetime.timedelta(days=30)

                    for reg in REGEXP_LIST:
                        regexp = re.compile(reg)
                        if regexp.findall(name):
                            vac_id = re.findall(r'\d{8}', url)
                            if len(vac_id) != 0 and vac_id[0] not in RR_ID_LIST:
                                if baseSalarymeta:
                                    if date > (CUR_DATE - DD):
                                        RR_ID_LIST.append(vac_id[0])
                                        print(name, date, baseSalarymeta["content"])
                                        desc = div.find("div", {"itemprop": "description"})

                                        if desc:
                                            jobs.append({
                                        "name": name.lstrip().rstrip(),
                                        "description": desc.text,
                                        "url": url
                                            })
                                elif baseSalaryspan:
                                    cur = baseSalaryspan.find("meta",{"itemprop":"currency"})
                                    salary = baseSalaryspan.find("meta",{"itemprop":"minValue"})
                                    if salary and cur:
                                        if (int(salary["content"])>50000 and cur["content"] == "RUB") or ((int(salary["content"])>500 and cur["content"] == "USD")):
                                            if date > (CUR_DATE - DD):
                                                print(name, date, salary["content"], cur["content"])
                                                RR_ID_LIST.append(vac_id[0])
                                                desc = div.find("div", {"itemprop": "description"})

                                                if desc:
                                                    jobs.append({
                                                        "name": name.lstrip().rstrip(),
                                                        "description": desc.text,
                                                        "url": url
                                                    })
    get_id_list_to_file()
    return jobs

if __name__ == "__main__":
    rr_parse()