import requests
import re
import csv
import datetime

from config import headers, REGEXP_LIST, ZP_VAC_LIST, ZP_ID_LIST

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

def get_list_from_file_zp_ru():
    with open("LIST_OF_VACANCIES_HH_RU.txt","r",encoding="utf-8") as file:
        for line in file:
            vac = line.replace(" ", "+")
            ZP_VAC_LIST.append(vac.strip())

def get_id_list_to_file():
    with open("ZP_ID_LIST.txt","w", encoding="utf-8") as file:
        for id in ZP_ID_LIST:
            file.write(str(id) + "\n")

def get_id_list_from_file():
    with open("ZP_ID_LIST.txt","r",encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines:
            ZP_ID_LIST.append(line.strip())

def zp_parse():
    get_id_list_from_file()
    jobs = []
    session = requests.Session()
    CUR_DATE = datetime.datetime.now()
    for vac in ZP_VAC_LIST:
        base_url = f"https://api.zarplata.ru/vacancies/?text={vac}&page=0"
        resp = session.get(base_url, headers=headers)

        json = resp.json()
        page = 0
        pages = int(json["pages"])

        while page < pages:
            print(page)
            base_url = f"https://api.zarplata.ru/vacancies/?text={vac}&page={page}"
            print(base_url)
            resp = session.get(base_url, headers=headers)

            json = resp.json()
            try:
                for item in json["items"]:
                    name = item["name"]
                    id = item["id"]
                    vac_url = item["alternate_url"]

                    try:
                        responsibility = item["snippet"]["responsibility"].replace("<highlighttext>","").replace("</highlighttext>","")
                    except:
                        responsibility = ""
                    try:
                        requirement = item["snippet"]["requirement"].replace("<highlighttext>", "").replace("</highlighttext>", "")
                    except:
                        requirement = ""
                    descr = responsibility+requirement

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
                                    if (cur == "RUR" and count > 50000) or (
                                            (cur == "USD" or cur == "EUR") and count > 500):
                                        if id not in ZP_ID_LIST:
                                            if date > (CUR_DATE - DD):
                                                ZP_ID_LIST.append(id)
                                                jobs.append({
                                                "name": name,
                                                "description": descr,
                                                "url": vac_url,
                                                "salary": f"{count} {cur}"
                                                })
                            else:
                                if id not in ZP_ID_LIST:
                                    if date > (CUR_DATE - DD):
                                        ZP_ID_LIST.append(id)
                                        jobs.append({
                                        "name": name,
                                        "description": descr,
                                        "url": vac_url,
                                        "salary": "Не указана"
                                        })
            except:
                pass

            page+=1
    get_id_list_to_file()
    res_list = [i for n, i in enumerate(jobs)
                if i not in jobs[n + 1:]]
    return res_list


if __name__ == "__main__":
    get_list_from_file()
    get_list_from_file_zp_ru()
    with open("../test_dir/zpru.csv", "w", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="|")
        writer.writerow(["Name", "Url"])
        for job in zp_parse():
            writer.writerow([job["name"], job["url"]])