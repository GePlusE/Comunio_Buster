# This is a class for a single Player

import requests
from bs4 import BeautifulSoup
from datetime import date, datetime


class Player:
    def __init__(self, player_ID):
        self.player_ID = player_ID
        self.dictionary = {}

    def get_base_data(self):
        """
        get all base data for a given PlayerID from
        www.com-analytics.de
        """
        # Preparation
        mainUrl = "https://www.com-analytics.de/player/"
        url = mainUrl + str(self.player_ID)
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        table = soup.find("table", attrs={"class": "table"})
        tableBody = table.find("tbody")
        rows = tableBody.find_all("tr")

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

        # Translate GER dict in ENG
        self.clean_dictionary()

    def get_injury_status(self):
        """
        get the injury status of a given player from
        www.fussballdaten.de
        """
        # get correct url from classic.comunio to fussballdaten.de
        def get_FuDa_url(self):
            mainUrl = "https://classic.comunio.de/bundesligaspieler/"
            url = mainUrl + str(player_ID) + "-" + name + ".html"
            page = requests.get(url)
            soup = BeautifulSoup(page.content, "html.parser")
            urlList = soup.find(class_="contenttext")

            urls = []
            for url in urlList.find_all(
                "a", href=True, text=re.compile("Fussballdaten.de")
            ):
                urls.append(url["href"])

            return urls[0]

    def clean_dictionary(self):
        """
        translates the german dictionary keys in english keys
        """
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
        }
        for key, value in translation_dictionary.items():
            try:
                self.dictionary[value] = self.dictionary.pop(key)
            except:
                pass
