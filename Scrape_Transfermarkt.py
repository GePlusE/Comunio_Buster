import urllib.request
import json

from bs4 import BeautifulSoup
from unidecode import unidecode

json_file = "player_dim.json"


def get_player_IDs(url):
    # get all PlayerIDs from a given Transfermarkt.de Club-URL

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
    # get all URL from all Germans first Bundesliga clubs

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
    # get all PlayerIDs from all Germans first Bundesliga Clubs from Transfermarkt.de

    club_urls = get_bundesliga_club_urls()
    dictionary = {}
    dictionary["IDs"] = {}
    for i in club_urls:
        main_url = "https://www.transfermarkt.de"
        url = main_url + i
        club_dict = get_player_IDs(url)
        for key, value in club_dict["IDs"].items():
            dictionary["IDs"][key] = value

    return dictionary


def load_data_to_json():
    # write the result from get_transfermarkt_data() to a json

    tm_data = get_transfermarkt_data()

    with open(json_file, "r+", encoding="UTF-8") as f:
        data = json.load(f)

    for key, value in tm_data["IDs"].items():
        last_name = value["Last-Name"]  # Müller
        first_name = value["First-Name"]  # Thomas
        full_name = value["Full-Name"]  # Thomas Müller
        alternative_name = first_name[0] + ". " + last_name  # T. Müller
        TM_ID = value["Transfermarkt-ID"]
        TM_url = value["Transfermarkt-URL"]
        non_matches = set()

        for key, value in data["IDs"].items():
            name = value["Comunio-Name"]
            split_name = name.split()[-1]
            match = [last_name, full_name, alternative_name]
            if name in match or split_name in match:
                data["IDs"][key]["Transfermarkt-ID"] = TM_ID
                data["IDs"][key]["Transfermarkt-URL"] = TM_url
                data["IDs"][key]["Last-Name"] = last_name
                data["IDs"][key]["First-Name"] = first_name
                data["IDs"][key]["Full-Name"] = full_name

    for key, value in data["IDs"].items():
        if value["Transfermarkt-ID"] == None:
            non_matches.add(value["Comunio-Name"])

    with open(json_file, "r+", encoding="UTF-8") as f:
        json.dump(data, f, sort_keys=True, indent=4)


def check_json_missing_TM_data():
    # check if a ID has missing Transfermarkt Data
    with open(json_file, "r+", encoding="UTF-8") as f:
        data = json.load(f)
        non_matches = {}

        for key, value in data["IDs"].items():
            if "Transfermarkt-ID" not in value:
                non_matches[key] = value
    print(non_matches)
    return non_matches


def add_Transfermarkt_data(dictionary):
    # add Transfermakt Data json
    tm_data = get_transfermarkt_data()

    with open(json_file, "r+", encoding="UTF-8") as f:
        data = json.load(f)

    for key, value in tm_data["IDs"].items():
        # Default characters
        last_name = value["Last-Name"]  # Müller
        first_name = value["First-Name"]  # Björn
        full_name = value["Full-Name"]  # Björn Müller
        alternative_name = first_name[0] + ". " + last_name  # B. Müller
        # Adjusted special characters.
        # e.g. ć to c
        last_name_adj = unidecode(last_name)  # Muller
        first_name_adj = unidecode(first_name)  # Bjorn
        full_name_adj = unidecode(full_name)  # Bjorn Muller
        alternative_name_adj = unidecode(alternative_name)  # B. Muller

        TM_ID = value["Transfermarkt-ID"]
        TM_url = value["Transfermarkt-URL"]
        non_matches_dict = {}

        for key, value in dictionary.items():
            name = value["Comunio-Name"]
            split_name = name.split()[-1]
            match = [
                last_name,
                full_name,
                alternative_name,
                last_name_adj,
                full_name_adj,
                alternative_name_adj,
            ]

            if name in match or split_name in match:
                # Match default names
                data["IDs"][key]["Transfermarkt-ID"] = TM_ID
                data["IDs"][key]["Transfermarkt-URL"] = TM_url
                data["IDs"][key]["Last-Name"] = last_name
                data["IDs"][key]["First-Name"] = first_name
                data["IDs"][key]["Full-Name"] = full_name
            if unidecode(name) in match or unidecode(split_name) in match:
                # Match adjusted names
                data["IDs"][key]["Transfermarkt-ID"] = TM_ID
                data["IDs"][key]["Transfermarkt-URL"] = TM_url
                data["IDs"][key]["Last-Name"] = last_name
                data["IDs"][key]["First-Name"] = first_name
                data["IDs"][key]["Full-Name"] = full_name

    for key, value in data["IDs"].items():
        try:
            if value["Transfermarkt-ID"] == None:
                non_matches_dict[key] = value
        except:
            pass
        try:
            if "Transfermarkt-ID" not in value:
                non_matches_dict[key] = value
        except:
            pass

    print(non_matches_dict)

    with open(json_file, "r+", encoding="UTF-8") as f:
        json.dump(data, f, sort_keys=True, indent=4)

