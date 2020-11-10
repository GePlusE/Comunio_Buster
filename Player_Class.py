# This is a class for a single Player

import requests
from bs4 import BeautifulSoup
from datetime import date, datetime
import re


class Player:
    def __init__(self, player_ID, club_ranks):
        self.player_ID = player_ID
        self.club_ranks = club_ranks
        self.dictionary = {}
        self.get_base_data()
        self.get_FuDa_data()
        self.get_StaCo_data()
        self.get_club_rank()

    def get_base_data(self):
        # get all base data for a given PlayerID from
        # www.com-analytics.de

        # Preparation
        mainUrl = "https://www.com-analytics.de/player/"
        url = mainUrl + str(self.player_ID)
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
        self.dictionary["save_date"] = str(date.today().strftime("%d.%m.%Y")).strip(".")
        self.dictionary["transaction_ID"] = str(date.today().strftime("%Y%m%d")) + str(
            self.dictionary["player_ID"]
        )

        # Translate GER dict in ENG & removes newline commands
        self.clean_dictionary()

    def get_StaCo_data(self):
        # get additional data from www.stats.comunio.de

        # Preparation
        main_url = "https://stats.comunio.de/profil.php?id="
        url = main_url + str(self.player_ID)
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

    def get_FuDa_data(self):
        # get additional data from www.fussballdaten.de

        # get correct url from classic.comunio->Player Details to fussballdaten.de
        def get_player_FuDa_url(self):
            try:
                main_url = "https://classic.comunio.de/bundesligaspieler/"
                url = (
                    main_url
                    + str(self.dictionary["player_ID"])
                    + "-"
                    + self.dictionary["Name"]
                    + ".html"
                )
                page = requests.get(url)
                soup = BeautifulSoup(page.content, "html.parser")
                url_list = soup.find(class_="contenttext")

                urls = []
                for url in url_list.find_all(
                    "a", href=True, text=re.compile("Fussballdaten.de")
                ):
                    urls.append(url["href"])

                return urls[0]
            except:
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

        self.dictionary["injury_status"] = get_injury_data(self)

    def get_club_rank(self):
        # get the national league rank from given dictionary
        try:
            rank = self.club_ranks[self.dictionary["club"]]
            self.dictionary["club_rank"] = rank
        except:
            pass

    def clean_dictionary(self):

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

