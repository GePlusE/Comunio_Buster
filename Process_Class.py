# This is a class for all generall functions of Comunio-Buster
import requests
from bs4 import BeautifulSoup


class Process:
    def __init__(self):
        self.player_ID_list = self.get_player_IDs()
        self.club_table_dict = self.get_club_ranks()

    def get_player_IDs(self):
        # get all PlayerIDs from com-analytics

        # //Preparation
        listUrl = "https://www.com-analytics.de/players/compare"
        req = requests.get(listUrl)
        soup = BeautifulSoup(req.content, "html.parser")

        # //get playerID"s
        options = soup.find("select", {"name": "list1"}).find_all("option")
        id_list = set(value.get("value") for value in options)
        id_list.remove(None)

        return id_list

    def get_club_ranks(self):
        # get the current german Bundesliga Ranking
        url = "https://stats.comunio.de/league_standings"
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        table = soup.find("table", attrs={"class": "rangliste autoColor"})
        rows = table.find_all("tr")
        # //Loop through Bundesliga Ranking + create dictionary
        dict = {}
        for row in rows:
            cols = row.find_all("td")
            cols = [ele.text.strip() for ele in cols]
            data = [ele for ele in cols if ele]  # //leere Werte loswerden

            if len(data) > 0:
                dict[data[1]] = data[0].replace(".", "")

        return dict
