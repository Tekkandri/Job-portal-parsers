from bs4 import BeautifulSoup
from time import sleep
import csv
import undetected_chromedriver as uc
import re
from config import REGEXP_LIST, AVITO_ID_LIST, AVITO_VAC_LIST

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

def get_list_from_file_avito():
    with open("LIST_OF_VACANCIES_REQUEST.txt", "r", encoding="utf-8") as file:
        for line in file:
            vac = line.replace(" ", "+")
            AVITO_VAC_LIST.append(vac.strip())

def get_id_list_to_file():
    with open("avito.txt","w", encoding="utf-8") as file:
        for id in AVITO_ID_LIST:
            file.write(str(id) + "\n")

def get_id_list_from_file():
    with open("avito.txt","r",encoding="utf-8") as file:
        AVITO_ID_LIST.clear()
        lines = file.readlines()
        for line in lines:
            AVITO_ID_LIST.append(line.strip())


def main():
    get_id_list_from_file()
    jobs = []
    base_url = "https://www.avito.ru/"
    driver = uc.Chrome(headless=True)
    for vac in AVITO_VAC_LIST:
        url = f"https://m.avito.ru/all/vakansii?cd=1&q={vac}&s=104"
        driver.get(url)
        sleep(3)
        soup = BeautifulSoup(driver.page_source, "lxml")
        items = soup.findAll("div", {"data-marker": "item"})
        for item in items:
            name = item.findNext("a")["title"]
            vac_url = base_url + item.findNext("a")["href"]
            salary = int(item.find("meta", {"itemprop": "price"})["content"])
            descr = item.find("meta",{"itemprop":"description"})["content"]

            for reg in REGEXP_LIST:
                regexp = re.compile(reg)
                if regexp.findall(name):
                    vac_id = item["data-item-id"]
                    if vac_id not in AVITO_ID_LIST:
                        if salary == 0 or salary > 50000:
                            print(name, salary)
                            AVITO_ID_LIST.append(vac_id)

                            jobs.append({
                                "name": name,
                                "description": descr,
                                "url": vac_url,
                            })
    get_id_list_to_file()
    driver.close()
    return jobs


if __name__ == "__main__":
    get_list_from_file()
    get_list_from_file_avito()
    with open("avito.csv","w",encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="|")
        writer.writerow(["Name", "Url", "Desc"])
        for job in main():
            writer.writerow([job["name"], job["url"], job["description"]])
