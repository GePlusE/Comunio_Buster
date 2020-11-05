# This is a class for all generall functions of Comunio-Buster
import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv
import concurrent.futures
import Player_Class


class Process:
    def __init__(self):
        self.player_ID_set = self.get_player_IDs()
        self.club_table_dict = self.get_all_club_ranks()
        self.dataset = []

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

    def get_all_club_ranks(self):
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

    def create_player_class(self, player_ID):
        player = Player_Class.Player(player_ID)
        self.dataset.append(player.dictionary)

    def multi_thread_load(self, given_set):
        # creates multiple player classes at once & loads the data for those player
        max_thread = 25  # a higher number increases processing speed
        player_IDs = given_set
        threads = min(max_thread, len(player_IDs))

        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(self.create_player_class, given_set)

    def write_to_csv(self, list_of_dict, filename):
        # writes dictionary to csv file and delete duplicates

        # loads historical data from csv
        df_base = pd.read_csv(filename, delimiter=";")

        # Convert dictionary into pandas dataframe
        df_new = pd.DataFrame(list_of_dict)

        # Combine df_base & df_new
        df_full = df_base.append(df_new, ignore_index=True)
        df_full.drop_duplicates(inplace=True)

        # write data frame to csv
        df_full.to_csv(filename, index=False, header=True, sep=";", encoding="utf-8")
