import urllib.request
import json
import logging

from bs4 import BeautifulSoup
from unidecode import unidecode


############################ Logging Settings ############################
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s %(levelname)s: %(filename)s: %(message)s")
# get formats from https://docs.python.org/3/library/logging.html#logrecord-attributes

file_handler = logging.FileHandler("LogFile.log")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
##########################################################################

json_file = "player_dim.json"


def get_player_IDs(club_url):
    # get all PlayerIDs from a given Transfermarkt.de Club-URL
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:63.0) Gecko/20100101 Firefox/63.0"
        }
        req = urllib.request.Request(url=club_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            page_html = response.read()

        soup = BeautifulSoup(page_html, "html.parser")
        players = soup.find_all("a", attrs={"class": "spielprofil_tooltip"})
        result = {}
        result["IDs"] = {}

        for i in players:
            try:
                full_name = i.get("title")
                ID = i.get("id")
                url = "https://www.transfermarkt.de" + i.get("href")

                result["IDs"][ID] = {}
                result["IDs"][ID]["Transfermarkt-ID"] = ID
                result["IDs"][ID]["Full-Name"] = full_name
                result["IDs"][ID]["First-Name"] = full_name.replace("-", " ").split()[
                    0
                ]  # split by spaces " " or dashes "-"
                result["IDs"][ID]["Last-Name"] = full_name.replace("-", " ").split()[
                    -1
                ]  # split by spaces " " or dashes "-"
                result["IDs"][ID]["Transfermarkt-URL"] = url
            except:
                logger.warning(
                    f"get_player_IDs failed. Could not load player_ids from specific url: {url}"
                )
            pass
        return result
    except:
        logger.warning(
            f"get_player_IDs failed in general. Could not load player_ids from {club_url}"
        )
        pass


def get_bundesliga_club_urls():
    # get all URL from all Germans first Bundesliga clubs
    try:
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
            try:
                url = i.get("href")
                result.append(url)
            except:
                logger.warning(
                    f"get_bundesliga_club_urls failed. Could not load player_ids from specific url: {url}"
                )
            pass
        return set(result)
    except:
        logger.warning(
            f"get_bundesliga_club_urls failed in general. Could not load player_ids from {bl_url}"
        )
        pass


def get_transfermarkt_data():
    # get all PlayerIDs from all Germans first Bundesliga Clubs from Transfermarkt.de
    # uses get_bundesliga_club_urls()
    # uses get_player_IDs()
    try:
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
    except:
        logger.warning(f"get_transfermarkt_data failed.")
        pass


def match_Transfermarkt_data():
    # matches Transfermakt Data to json
    # uses get_transfermarkt_data
    tm_data = get_transfermarkt_data()

    with open(json_file, "r+", encoding="UTF-8") as f:
        data = json.load(f)

    try:
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

            for key, value in data["IDs"].items():
                name = value["Comunio-Name"]
                split_name = name.replace("-", " ").split()[-1]
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
                    continue
                if unidecode(name) in match or unidecode(split_name) in match:
                    # Match adjusted names
                    data["IDs"][key]["Transfermarkt-ID"] = TM_ID
                    data["IDs"][key]["Transfermarkt-URL"] = TM_url
                    data["IDs"][key]["Last-Name"] = last_name
                    data["IDs"][key]["First-Name"] = first_name
                    data["IDs"][key]["Full-Name"] = full_name

        # add all IDs with missing TM Data to non_match_dict
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

        # if non_match_dict is not empty write to LogFile.log
        if bool(non_matches_dict):
            nl = "\n"
            count = len(non_matches_dict)
            get_details = f"import Scrape_Transfermarkt as STM{nl}STM.check_json_missing_TM_data()"
            logger.exception(
                f"In total {count:,.0f} IDs could not be matched. Use following snippet for details:{nl}{get_details}"
            )
    except:
        logger.warning(f"match_Transfermarkt_data failed.")
        pass

    with open(json_file, "r+", encoding="UTF-8") as f:
        f.seek(0)
        json.dump(data, f, sort_keys=True, indent=4)
        f.truncate()


def check_json_missing_TM_data():
    # check if a ID has missing Transfermarkt Data
    # not used inside any other function
    with open(json_file, "r+", encoding="UTF-8") as f:
        data = json.load(f)
    non_matches = {}

    for key, value in data["IDs"].items():
        if "Transfermarkt-ID" not in value:
            non_matches[key] = value
    print(non_matches)

