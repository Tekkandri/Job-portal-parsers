import requests
from bs4 import BeautifulSoup
import re
import csv

from config import REGEXP_LIST, CAREERIST_ID_LIST, CAREERIST_VAC_LIST, headers

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

def get_list_from_file_careerist():
    with open("LIST_OF_VACANCIES_REQUEST.txt", "r", encoding="utf-8") as file:
        CAREERIST_VAC_LIST.clear()
        for line in file:
            vac = line.replace(" ", "-")
            CAREERIST_VAC_LIST.append(vac.strip())

def get_id_list_to_file():
    with open("careerist.txt","w", encoding="utf-8") as file:
        for id in CAREERIST_ID_LIST:
            file.write(str(id) + "\n")

def get_id_list_from_file():
    with open("careerist.txt","r",encoding="utf-8") as file:
        CAREERIST_ID_LIST.clear()
        lines = file.readlines()
        for line in lines:
            CAREERIST_ID_LIST.append(line.strip())

def main():
    get_id_list_from_file()
    jobs = []
    session = requests.session()
    for vac in CAREERIST_VAC_LIST:
        url = f"https://careerist.ru/search/?text={vac}&category=vacancy&region=rossia-80000002"
        print(url)
        resp = session.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "lxml")
        try:
            last_page_url = soup.find("ul",{"class":"pagination"}).find_all("li",{"class":"page-item"})[-1].find("a")["href"]
            last_page = int(re.findall(r'page=\d+', last_page_url)[0].split("=")[1])
            print(last_page)
        except:
            last_page = 1

        for page in range(1, last_page+1):
            url = f"https://careerist.ru/search/?text={vac}&category=vacancy&region=rossia-80000002&page={page}"
            print(url)
            resp = session.get(url, headers=headers)
            soup = BeautifulSoup(resp.text, "lxml")
            divs = soup.find_all("div", {"class":"list","id":True})
            for div in divs:
                name = div.find("div",{"class":"list-block"}).find_all("p",{"class":"card-text"})[0].text
                vac_url = div.find("div",{"class":"list-block"}).find_all("p",{"class":"card-text"})[0].find("a")["href"]
                descr = div.find("div",{"class":"list-block"}).find_all("p",{"class":"card-text"})[-1].text
                salary_str = div.find("div",{"class":"list-block"}).find_all("p",{"class":"card-text"})[2].text.replace("&nbsp;","").replace(" ","")
                salary_lst = re.findall("от\d+",salary_str)
                salary = 0
                if len(salary_lst) != 0:
                    salary = salary_lst[0][2:]

                for reg in REGEXP_LIST:
                    regexp = re.compile(reg)
                    if regexp.findall(name):
                        vac_id = re.findall(r'\d{8}', vac_url)
                        if len(vac_id) != 0 and vac_id[0] not in CAREERIST_ID_LIST:
                            if (int(salary) > 50000) or len(salary_str) == 1:
                                CAREERIST_ID_LIST.append(vac_id[0])

                                jobs.append({
                                "name": name,
                                "description": descr,
                                "url": vac_url
                                })
    get_id_list_to_file()
    return jobs


if __name__ == "__main__":
    get_list_from_file()
    get_list_from_file_careerist()
    with open("careerist.csv", "w", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="|")
        writer.writerow(["Name", "Url", "Desc"])
        for job in main():
            writer.writerow([job["name"], job["url"], job["description"]])