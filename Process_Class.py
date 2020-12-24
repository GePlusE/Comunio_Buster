import requests
import pandas as pd
import csv
import concurrent.futures
import Player_Class
import logging
import Quality_Checks as qc

from bs4 import BeautifulSoup


############################ Logging Settings ############################
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s %(levelname)s: %(filename)s: %(message)s")
# get formats from https://docs.python.org/3/library/logging.html#logrecord-attributes

file_handler = logging.FileHandler("LogFile.log")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
##########################################################################


class Process:
    def __init__(self):
        try:
            self.player_ID_set = self.get_player_IDs()
            self.club_table_dict = self.get_all_club_ranks()
            self.dataset = []
        except:
            logger.exception(f"Initialization failed")
            raise

    def get_player_IDs(self):
        try:
            # get all PlayerIDs from com-analytics

            # //Preparation
            url = "https://www.com-analytics.de/players/compare"
            # Check URL status
            qc.check_url_status(url, "playerIDs")
            # Scrapping
            req = requests.get(url)
            soup = BeautifulSoup(req.content, "html.parser")

            # //get playerID"s
            options = soup.find("select", {"name": "list1"}).find_all("option")
            id_list = set(value.get("value") for value in options)
            id_list.remove(None)

            return id_list
        except:
            logger.exception(f"get_player_IDs failed")
            raise

    def get_all_club_ranks(self):
        try:
            # get the current german Bundesliga Ranking
            url = "https://stats.comunio.de/league_standings"
            # Check URL status
            qc.check_url_status(url, "club_ranks")
            # Scrapping
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
            # translate club names
            club_transl = {
                "1899 Hoffenheim": "TSG Hoffenheim",
                "1. FC Union Berlin": "1.FC Union Berlin",
                "Borussia M'gladbach": "Borussia Mönchengladbach",
                "Arminia Bielefeld": "DSC Arminia Bielefeld",
                "SC Freiburg": "Sport-Club Freiburg",
            }

            for key, value in club_transl.items():
                try:
                    dict[value] = dict.pop(key)
                except:
                    pass
            return dict
        except:
            logger.exception(f"get_all_club_ranks failed")
            raise

    def create_player_class(self, player_ID):
        player = Player_Class.Player(player_ID, self.club_table_dict)
        self.dataset.append(player.dictionary)

    def multi_thread_load(self, given_set):
        # creates multiple player classes at once & loads the data for those player
        max_thread = 25  # a higher number increases processing speed
        player_IDs = given_set
        threads = min(max_thread, len(player_IDs))

        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(self.create_player_class, given_set)

    def sequential_load(self, given_set):
        # for i in given_set:
        for i in list(given_set):
            self.create_player_class(i)

    def write_to_csv(self, list_of_dict, filename):
        try:
            # writes dictionary to csv file and delete duplicates

            # loads historical data from csv
            df_base = pd.read_csv(filename, delimiter=";")
            df_base_rowcount = len(df_base.index)
            # Convert dictionary into pandas dataframe
            df_new = pd.DataFrame(list_of_dict)
            df_new_rowcount = len(df_new.index)
            # Combine df_base & df_new
            df_full = df_base.append(df_new, ignore_index=True)
            df_full.drop_duplicates(inplace=True)
            # Calculate entries
            df_full_rowcount = len(df_full.index)
            new_rowcount = df_full_rowcount - df_base_rowcount
            logger.info(
                f"Total entries: {df_full_rowcount:,.0f} // Scrapped {df_new_rowcount:,.0f} entries successfully thereof {new_rowcount:,.0f} brand new entries"
            )
            # write data frame to csv
            df_full.to_csv(
                filename, index=False, header=True, sep=";", encoding="utf-8"
            )
        except:
            logger.exception(f"write_to_csv failed")
            raise

    def combine_files(self, old_file, new_file, name_of_created_file):

        df1 = pd.read_csv(old_file, delimiter=";", low_memory=False)
        df2 = pd.read_csv(new_file, delimiter=";", low_memory=False)

        df3 = pd.concat([df2, df1])

        df3.to_csv(name_of_created_file, index=False)


if __name__ == "__main__":
    pass
