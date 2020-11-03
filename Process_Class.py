# This is a class for all generall functions of Comunio-Buster
import requests
from bs4 import BeautifulSoup


class Process:
    def __init__(self):
        self.player_ID_list = self.get_player_IDs()

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
