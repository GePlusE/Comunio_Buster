import requests
import re
import logging
import json

from bs4 import BeautifulSoup
from datetime import date, datetime


############################ Logging Settings ############################
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s %(levelname)s: %(filename)s: %(message)s")
# get formats from https://docs.python.org/3/library/logging.html#logrecord-attributes

file_handler = logging.FileHandler("LogFile.log")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
##########################################################################

player_dim_file = "player_dim.json"

# TODO: Check url status
# TODO: Check if new dictionary attribute is available
# TODO: Check if dictionary is empty -> LogFile


class Player:
    def __init__(self, player_ID, club_ranks):
        try:
            self.dim_dictionary = {}
            self.player_ID = player_ID
            self.existing_data = self.load_from_json()
            self.club_ranks = club_ranks
            self.dictionary = {}
            self.get_base_data()
            self.get_FuDa_data()
            self.get_StaCo_data()
            self.get_club_rank()
            # create dim_dictionary for json load
            self.dim_dictionary["Comunio-ID"] = self.player_ID
            self.dim_dictionary["Comunio-Name"] = self.dictionary["Name"]
            self.write_dim_json()
        except:
            logger.warning(f"Initialization of ID-{self.player_ID} failed.")
            pass

    def get_base_data(self):
        # get all base data for a given PlayerID from
        # www.com-analytics.de
        name = "Com-Analytics-URL"
        # Preparation use URL in dim_player.json if existing else get new URL
        if self.existing_data[name]:
            url = self.existing_data[name]
        else:
            main_url = "https://www.com-analytics.de/player/"
            url = main_url + str(self.player_ID)
        try:
            page = requests.get(url)
            soup = BeautifulSoup(page.content, "html.parser")
            table = soup.find("table", attrs={"class": "table"})
            table_body = table.find("tbody")
            rows = table_body.find_all("tr")

            # Get base data & add to dictionary
            for row in rows:
                cols = row.find_all("td")
                cols = [ele.text.strip() for ele in cols]
                self.dictionary[cols[0]] = cols[1]

            # Add further details to dictionary
            self.dictionary["player_ID"] = self.player_ID
            self.dictionary["save_date"] = str(date.today().strftime("%d.%m.%Y")).strip(
                "."
            )
            self.dictionary["transaction_ID"] = str(
                date.today().strftime("%Y%m%d")
            ) + str(self.dictionary["player_ID"])

            # Translate GER dict in ENG & removes newline commands
            self.clean_dictionary()

            # Add url to self.dim_dictionary
            self.dim_dictionary[name] = url
        except:
            logger.warning(f"Getting base data for ID-{self.player_ID} failed. {url}")
            pass

    def get_StaCo_data(self):
        # get additional data from www.stats.comunio.de
        name = "StaCo-URL"
        # Preparation
        # Preparation use URL in dim_player.json if existing else get new URL
        if self.existing_data[name]:
            url = self.existing_data[name]
        else:
            main_url = "https://stats.comunio.de/profil.php?id="
            url = main_url + str(self.player_ID)
        try:
            page = requests.get(url)
            soup = BeautifulSoup(page.content, "html.parser")
            table = soup.find(class_="awards")
            if table == None:  # Check if player as any awards
                self.dictionary["fav_team_nomination"] = None
                self.dictionary["dreamteam_nomination"] = None
            else:
                rows = table.find_all("img", title=True)
                # Lopp through awards
                for row in rows:
                    cols = row.get("title")
                    if "Favorisierte" in cols:
                        self.dictionary["fav_team_nomination"] = int(cols[-2:])
                    elif "Dreamteam" in cols:
                        self.dictionary["dreamteam_nomination"] = int(cols[-2:])
                    else:
                        pass
            # Add url to self.dim_dictionary
            self.dim_dictionary[name] = url
        except:
            logger.warning(f"Getting StaCo data for ID-{self.player_ID} failed. {url}")
            pass

    def get_FuDa_data(self):
        # get additional data from www.fussballdaten.de
        name = "FuDa-URL"
        # get correct url from classic.comunio->Player Details to fussballdaten.de
        def get_player_FuDa_url(self):
            # Preparation use URL in dim_player.json if existing else get new URL
            if self.existing_data[name]:
                url = self.existing_data[name]
            else:
                main_url = "https://classic.comunio.de/tradableInfo.phtml?tid="
                url = main_url + str(self.dictionary["player_ID"])
            try:
                page = requests.get(url)
                soup = BeautifulSoup(page.content, "html.parser")
                url_list = soup.find(class_="contenttext")

                urls = []
                for url in url_list.find_all(
                    "a", href=True, text=re.compile("Fussballdaten.de")
                ):
                    urls.append(url["href"])
                result_url = urls[0]

                # Add url to self.dim_dictionary
                self.dim_dictionary[name] = result_url
                return result_url

            except:
                # # TODO: Temporary deactivated due to known issue which will be fixed soon
                # logger.warning(
                #     f"Getting FuDa URL for ID-{self.player_ID} failed. Check FuDa link on {url}"
                # )
                self.dim_dictionary[name] = None
                pass

        def get_injury_data(self):
            # get inury data from Fussballdaten.de
            try:
                url = get_player_FuDa_url(self)
                page = requests.get(url)
                soup = BeautifulSoup(page.content, "html.parser")
                parts = str(soup.find(class_="spieler-status"))
                status = None
                if "red" in parts:
                    status = "injured/suspended"
                elif "green" in parts:
                    status = "fit"
                return status
            except:
                pass

        try:
            self.dictionary["injury_status"] = get_injury_data(self)
        except:
            logger.warning(f"Getting injury data for ID-{self.player_ID} failed.")
            pass

    def get_club_rank(self):
        # get the national league rank from given dictionary
        try:
            rank = self.club_ranks[self.dictionary["club"]]
            self.dictionary["club_rank"] = rank
        except:
            logger.warning(f"Getting club rank for ID-{self.player_ID} failed.")
            pass

    def clean_dictionary(self):
        try:
            remove_list = ["N/A", "na", "NA", "n.a", "nv", "n.v.", "nan", "none"]
            witout_dot = [
                "value",
                "prognosis",
                "value_change_L7D",
                "team_value_change_L7D",
                "value_change_L3M",
            ]
            translation_dictionary = {
                "Verein": "club",
                "Marktwert": "value",
                "Prognose1": "prognosis",
                "Gesamtpunkte": "total_points",
                "Punktevolatilität": "points_volatility",
                "Historische Punkteausbeute": "historical_point_yield",
                "Punkte am letzten Spieltag": "last_points",
                "Empfehlung": "suggestion",
                "Änderung (7 Tage)": "value_change_L7D",
                "Team-Änderung (7 Tage)": "team_value_change_L7D",
                "Änderung (3 Monate)": "value_change_L3M",
                "Team-Änderung (3 Monate)": "team_value_change_L3M",
                "Bewertete Spiele": "rated_games",
                "Verletzungsanfälligkeit": "injury_rate",
            }  # translates the german dictionary keys in english keys

            for key, value in translation_dictionary.items():
                try:
                    self.dictionary[value] = self.dictionary.pop(key)
                except:
                    pass
            # delete newline character
            for key, value in self.dictionary.items():
                try:
                    self.dictionary[key] = value.replace("\n", "")
                except:
                    pass
            # remove dots from values
            for key, value in self.dictionary.items():
                if key in witout_dot:
                    self.dictionary[key] = value.replace(".", "")
            # replace specific strings with None
            for key, value in self.dictionary.items():
                if value in remove_list:
                    self.dictionary[key] = ""
        except:
            logger.exception(f"Cleaning dictionary of ID-{self.player_ID} failed.")
            pass

    def write_dim_json(self):
        # write dim_dictionary to json
        # mainly used to record website name (key) & exact URL (value)
        ID = self.player_ID
        dictionary = self.dim_dictionary
        forbidden_input = [None, "", " ", "NaN"]
        # check if dictionary contains valid input
        for key, value in dictionary.items():
            if key in forbidden_input or value in forbidden_input:
                if key == "FuDa-URL":
                    pass
                else:
                    logger.exception(
                        f"ID-{self.player_ID}: Key: {key} or Value: {value} is invalid"
                    )
                pass
            try:
                with open(player_dim_file, "r+", encoding="utf-8") as f:
                    data = json.load(f)
                    # If ID exist in json only change values or add new key & value
                    if ID in data["IDs"]:
                        for key, value in dictionary.items():
                            try:
                                data["IDs"][ID][key] = value
                            except:
                                logger.exception(
                                    f"ID-{self.player_ID}: Writing key: {key} or value: {value} to file: {player_dim_file} failed."
                                )
                                pass
                        f.seek(0)
                        json.dump(data, f, sort_keys=True, indent=4)
                        f.truncate()
                    # ID does not exist add complete dict
                    else:
                        data["IDs"][ID] = dictionary
                        f.seek(0)
                        json.dump(data, f, sort_keys=True, indent=4)
                        f.truncate()
            except:
                logger.warning(f"ID-{self.player_ID}: write_dim_json failed!")
                pass

    def load_from_json(self):
        # load specific json data for player_ID
        result = {}
        try:
            with open(player_dim_file, "r+", encoding="utf-8") as f:
                data = json.load(f)
            result = data["IDs"][self.player_ID]
        except:
            logger.info(f"ID-{self.player_ID}: load_from_json failed.")
            result["Com-Analytics-URL"] = None
            result["FuDa-URL"] = None
            result["StaCo-URL"] = None
            result["Transfermarkt-URL"] = None
            result["Transfermarkt-ID"] = None
            pass
        return result
