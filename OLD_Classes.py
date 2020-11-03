import concurrent.futures
import csv
import os
import re
import time
from datetime import date, datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup


class Data:
    def __init__(self, csv_filename):
        self.csv_filename = csv_filename

        # //Create path for csv file -> necessary to run via daily autorun
        self.filePath1 = os.path.dirname(os.path.realpath(__file__))
        self.factPlayerCSV = os.path.join(self.filePath1, self.csv_filename)

    def get_PlayerIDs(self):
        """
        get all PlayerIDs from com-analytics
        """
        # //Preparation
        listUrl = "https://www.com-analytics.de/players/compare"
        req = requests.get(listUrl)
        soup = BeautifulSoup(req.content, "html.parser")

        # //get playerID"s
        options = soup.find("select", {"name": "list1"}).find_all("option")
        id_list = set(value.get("value") for value in options)
        id_list.remove(None)

        # //Write to LogFile.txt
        today = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print(today + ": " + str(len(id_list)) + " PlayerIDs found")

        return id_list

    def get_BaseData(self, playerID):
        """
        get all base Data for a given PlayerID
        """

        # //Preparation
        mainUrl = "https://www.com-analytics.de/player/"
        url = mainUrl + str(playerID)
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        table = soup.find("table", attrs={"class": "table"})
        tableBody = table.find("tbody")
        rows = tableBody.find_all("tr")

        # //Add base data
        data = []
        for row in rows:
            cols = row.find_all("td")
            cols = [ele.text.strip() for ele in cols]
            data.append([ele for ele in cols if ele])  # //leere Werte loswerden
        data.append(["PlayerID", playerID])

        # //Add injury status
        try:
            data.append(
                [
                    "injuryStatus",
                    self.get_InjuryStatus(
                        self.get_PlayerUrl_FuDa(playerID, data[0][1])
                    ),
                ]
            )
        except:
            data.append(["injuryStatus", None])

        # //Add club rank
        try:
            dict = self.get_ClubRank()
            rank = dict.get(data[2][1])
            data.append(["clubRank", rank])
        except:
            data.append(["clubRank", None])

        # //Add nomination count of Dreamteam and FavoriteTeam
        # ///Dreamteam
        try:
            dict = self.get_PlayerData_StaCo(playerID)
            data.append(["CountDreTeam", dict.get("dreTeam")])
        except:
            data.append(["CountDreTeam", None])
        # ///FavoriteTeam
        try:
            dict = self.get_PlayerData_StaCo(playerID)
            data.append(["CountFavTeam", dict.get("favTeam")])
        except:
            data.append(["CountFavTeam", None])

        # //Translate data into dictionary
        dictionary = {i[0]: i[-1] for i in data}

        self.save_Data_to_FactCsv(dictionary)
        time.sleep(5)

    def save_Data_to_FactCsv(self, dataset):
        """
        save all the data to the csv file
        """
        # //Define list
        playerID = int(dataset.get("PlayerID"))
        name = dataset.get("Name")
        position = dataset.get("Position")
        club = dataset.get("Verein")
        value = int(dataset.get("Marktwert").replace(".", ""))
        prognosis = int(dataset.get("Prognose1").replace(".", ""))
        if dataset.get("Gesamtpunkte") == "N/A":
            totalPoints = 0
        else:
            totalPoints = int(dataset.get("Gesamtpunkte"))
        pointVolatility = None
        if dataset.get("Punkte am letzten Spieltag") == "N/A":
            lastPoints = 0
        else:
            lastPoints = int(dataset.get("Punkte am letzten Spieltag"))
        suggestion = dataset.get("Empfehlung")
        ratedGames = int(dataset.get("Bewertete Spiele"))
        injuryRate = dataset.get("Verletzungsanfälligkeit")
        injuryStatus = dataset.get("injuryStatus")
        clubRank = dataset.get("clubRank")
        saveDate = date.today().strftime("%d.%m.%Y")
        ID = str(date.today().strftime("%Y%m%d")) + str(playerID)
        dreamTeam = dataset.get("CountDreTeam")
        favTeam = dataset.get("CountFavTeam")

        # //Write list to csv
        with open(self.factPlayerCSV, "a") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(
                [
                    ID,
                    playerID,
                    name,
                    position,
                    club,
                    value,
                    prognosis,
                    totalPoints,
                    pointVolatility,
                    lastPoints,
                    suggestion,
                    ratedGames,
                    injuryRate,
                    saveDate,
                    injuryStatus,
                    clubRank,
                    dreamTeam,
                    favTeam,
                ]
            )

    # //Step B3
    def get_Multiple_FactData(self):
        """
        collect data from multiple player at once
        """
        MAX_THREADS = 10  # //higher number increases processing speed
        playerIDs = self.get_PlayerIDs()
        threads = min(MAX_THREADS, len(playerIDs))

        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(self.get_BaseData, playerIDs)

    def get_PlayerUrl_FuDa(self, playerID, name):
        """
        get data from Fussballdaten.de
        """
        mainUrl = "https://classic.comunio.de/bundesligaspieler/"
        url = mainUrl + str(playerID) + "-" + name + ".html"
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        urlList = soup.find(class_="contenttext")

        urls = []
        for url in urlList.find_all(
            "a", href=True, text=re.compile("Fussballdaten.de")
        ):
            urls.append(url["href"])

        return urls[0]

    def get_PlayerData_StaCo(self, playerID):
        """
        get data from Stats.Comunio.de
        """
        # //Preparation
        mainUrl = "https://stats.comunio.de/profil.php?id="
        url = mainUrl + str(playerID)
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        table = soup.find(class_="playerdata stretch autoColor")
        rows = table.find_all("tr")
        # //Loop through table elements
        data = []
        for row in rows:
            cols = row.find_all("td")
            for i in cols:
                try:
                    data.append(i.find("img", title=True).get("title"))
                except:
                    pass
        # //Setting up default dictionary
        dict = {}
        dict["club"] = data[0]
        dict["favTeam"] = 0
        dict["dreTeam"] = 0
        # //Adjust dictionary
        if len(data) > 1:
            for i in data:
                if "Favorisierte Spieler" in i:
                    dict["favTeam"] = int(i[-2:])
                elif "Dreamteam" in i:
                    dict["dreTeam"] = int(i[-2:])

        return dict

    def get_InjuryStatus(self, link):
        """
        get injury data from FuDa-link + playerID
        """
        url = link
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        parts = str(soup.find(class_="spieler-status"))
        status = None
        if "red" in parts:
            status = "injured/suspended"
        elif "green" in parts:
            status = "fit"
        return status

    def get_ClubUrl_FuDa(self, link):
        """
        get Club Url from FußballDaten.de
        """
        playerUrl = link
        page = requests.get(playerUrl)
        soup = BeautifulSoup(page.content, "html.parser")
        step1 = soup.find(class_="box person")
        step2 = step1.find("a", href=True)
        urlPrefix = step2["href"]
        url = "https://www.fussballdaten.de/" + urlPrefix
        return url

    def get_ClubRank(self):
        """
        get Club ranking from stats.comunio.de
        """
        url = "https://stats.comunio.de/league_standings"
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        table = soup.find("table", attrs={"class": "rangliste autoColor"})
        rows = table.find_all("tr")
        # //Loop through Bundesliga Ranking + save to dictionary
        dict = {}
        for row in rows:
            cols = row.find_all("td")
            cols = [ele.text.strip() for ele in cols]
            data = [ele for ele in cols if ele]  # //leere Werte loswerden

            if len(data) > 0:
                dict[data[1]] = data[0].replace(".", "")

        return dict

    def row_Count(self, filename):
        """
        Count rows in given file
        """
        with open(filename) as f:
            count = sum(1 for line in f)
        return count

    def clean_csv(self, filename):
        """
        Removes duplicates from given csv file
        """

        with open(filename) as f:
            count0 = sum(1 for line in f)
        df = pd.read_csv(filename)
        df.drop_duplicates(inplace=True)
        df.to_csv(filename, index=False)

        with open(filename) as f:
            count1 = sum(1 for line in f)

        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        if (count0 - count1) > 0:
            print(
                timestamp + f": Cleaned {count0 - count1} duplicates",
                file=open("LogFile.txt", "a"),
            )

    def update_csv(self):
        """
        runs all neccessary functions to update the csv file
        Including entries in LogFile.
        """
        t0 = time.time()
        self.clean_csv(self.factPlayerCSV)
        count0 = self.row_Count(self.factPlayerCSV)
        today = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        self.get_Multiple_FactData()

        t1 = time.time()
        count1 = self.row_Count(self.factPlayerCSV)

        # //Write to LogFile.txt
        print(
            today
            + f": Duration: {round(t1 - t0, 2)} seconds // New Entries: {count1 - count0}",
            file=open("LogFile.txt", "a"),
        )
        today = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print(
            today
            + f": Duration: {round(t1 - t0, 2)} seconds // New Entries: {count1 - count0}."
        )

