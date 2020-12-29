import urllib.request
from bs4 import BeautifulSoup
import json


def get_player_IDs(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:63.0) Gecko/20100101 Firefox/63.0"
    }
    req = urllib.request.Request(url=url, headers=headers)
    with urllib.request.urlopen(req) as response:
        page_html = response.read()

    soup = BeautifulSoup(page_html, "html.parser")
    players = soup.find_all("a", attrs={"class": "spielprofil_tooltip"})
    result = {}
    result["IDs"] = {}

    # result["IDs"]["ID"]["Key"] = "Value"
    # print(result)
    for i in players:
        full_name = i.get("title")
        ID = i.get("id")
        url = "https://www.transfermarkt.de" + i.get("href")

        result["IDs"][ID] = {}
        result["IDs"][ID]["Transfermarkt-ID"] = ID
        result["IDs"][ID]["Full-Name"] = full_name
        result["IDs"][ID]["First-Name"] = full_name.split()[0]
        result["IDs"][ID]["Last-Name"] = full_name.split()[-1]
        result["IDs"][ID]["Transfermarkt-URL"] = url
    return result


def get_bundesliga_club_urls():
    bl_url = "https://www.transfermarkt.de/1-bundesliga/startseite/wettbewerb/L1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:63.0) Gecko/20100101 Firefox/63.0"
    }
    req = urllib.request.Request(url=bl_url, headers=headers)
    with urllib.request.urlopen(req) as response:
        page_html = response.read()

    soup = BeautifulSoup(page_html, "html.parser")
    table = soup.find("table", attrs={"class": "items"})
    clubs = table.find_all("a", attrs={"class": "vereinprofil_tooltip"})
    result = []
    for i in clubs:
        url = i.get("href")
        result.append(url)
    return set(result)


def get_transfermarkt_data():
    club_urls = get_bundesliga_club_urls()
    dictionary = {}
    dictionary["IDs"] = {}
    for i in club_urls:
        main_url = "https://www.transfermarkt.de"
        url = main_url + i
        club_dict = get_player_IDs(url)
        for key, value in club_dict["IDs"].items():
            dictionary["IDs"][key] = value

    with open("test2.json", "r+", encoding="UTF-8") as f:
        json.dump(dictionary, f, sort_keys=True, indent=4)

    return dictionary

