import requests
from bs4 import BeautifulSoup
import re
import csv

from config import REGEXP_LIST, JOBLAB_ID_LIST, JOBLAB_VAC_LIST, headers

symb_dict = {
"а":	"%E0",
"б":	"%E1",
"в":	"%E2",
"г":	"%E3",
"д":	"%E4",
"е":	"%E5",
"ё":	"%B8",
"ж":	"%E6",
"з":	"%E7",
"и":	"%E8",
"й":	"%E9",
"к":	"%EA",
"л":	"%EB",
"м":	"%EC",
"н":	"%ED",
"о":	"%EE",
"п":	"%EF",
"р":	"%F0",
"с":	"%F1",
"т":	"%F2",
"у":	"%F3",
"ф":	"%F4",
"х":	"%F5",
"ц":	"%F6",
"ч":	"%F7",
"ш":	"%F8",
"щ":	"%F9",
"ъ":	"%FA",
"ы":	"%FB",
"ь":	"%FC",
"э":	"%FD",
"ю":	"%FE",
"я":	"%FF"
}

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

def get_list_from_file_joblab():
    with open("LIST_OF_VACANCIES_REQUEST.txt", "r", encoding="utf-8") as file:
        JOBLAB_VAC_LIST.clear()
        for line in file:
            vac = line.replace(" ", "+")
            JOBLAB_VAC_LIST.append(vac.strip())

def get_id_list_to_file():
    with open("joblab.txt","w", encoding="utf-8") as file:
        for id in JOBLAB_ID_LIST:
            file.write(str(id) + "\n")

def get_id_list_from_file():
    with open("joblab.txt","r",encoding="utf-8") as file:
        JOBLAB_ID_LIST.clear()
        lines = file.readlines()
        for line in lines:
            JOBLAB_ID_LIST.append(line.strip())

def get_enother_encode(vac: str):
    result = ""
    for sym in vac:
        if sym in symb_dict.keys():
            result += symb_dict[sym]
        else:
            result += sym
    return result

def main():
    get_id_list_from_file()
    jobs = []
    session = requests.session()
    for vac in JOBLAB_VAC_LIST:

        encode_vac = get_enother_encode(vac.lower())

        url = f"https://joblab.ru/search.php?r=vac&srprofecy={encode_vac}&kw_w2=1&srzpmin=&srregion=100&srcity=&srcategory=&submit=1"
        print(url)
        resp = session.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "lxml")
        last_page = 1
        try:
            last_page = int(soup.find_all("a", {"class":"pager"})[-1].text)
            print(last_page)
        except:
            pass

        for page in range(1, last_page+1):
            url = f"https://joblab.ru/search.php?r=vac&srprofecy={encode_vac}&kw_w2=1&srzpmin=&srregion=100&page={page}&srcity=&srcategory=&submit=1&pred=30"
            print(url)
            resp = session.get(url, headers=headers)
            soup = BeautifulSoup(resp.text, "lxml")

            profs = soup.find_all("p",{"class":"prof"})
            descs = soup.find_all("p",{"class":"descr2"})
            salaries = soup.find_all("td",{"class":"td-to-div-zp"})

            for i in range(len(profs)):
                name = profs[i].find("a").text
                vac_url = "https://joblab.ru" + profs[i].find("a")["href"]
                desc = descs[i].text
                salary_lst = re.findall(r"\d+",salaries[i].text.replace(" ",""))
                salary = 0
                if len(salary_lst) != 0:
                    salary = int(salary_lst[0])

                for reg in REGEXP_LIST:
                    regexp = re.compile(reg)
                    if regexp.findall(name):
                        vac_id = re.findall(r'\d{8}', vac_url)
                        if len(vac_id) != 0 and vac_id[0] not in JOBLAB_ID_LIST:
                            if salary > 50000 or len(salary_lst) == 0:
                                JOBLAB_ID_LIST.append(vac_id[0])

                                jobs.append({
                                "name": name,
                                "description": desc,
                                "url": vac_url,
                                })

    get_id_list_to_file()
    return jobs

if __name__ == "__main__":
    get_list_from_file()
    get_list_from_file_joblab()
    with open("joblab.csv", "w", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="|")
        writer.writerow(["Name", "Url", "Desc"])
        for job in main():
            writer.writerow([job["name"], job["url"], job["description"]])