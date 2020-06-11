import concurrent.futures
import csv
import os
import re
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

"""
- A Steps:      Get all PlayerIDs from com-analytics.de
- B Steps:      Load Base Data from com-analytics.de
- C Steps:      Load Injury Data via classic.comunio.de to Fussballdaten.de
- D Steps:      Load Club Rank via Fussballdaten.de
- Final Step:   Run one Load to update all Data 
"""

# //Create path for csv file -> necessary to run via daily autorun
filePath1 = os.path.dirname(os.path.realpath(__file__))
factPlayerCSV = os.path.join(filePath1, "fact_Player.csv")


# //Step A1
def getPlayerIDs():
    # //Preparation
    listUrl = "https://www.com-analytics.de/players/compare"
    req = requests.get(listUrl)
    soup = BeautifulSoup(req.content, "html.parser")

    # //get playerID"s
    options = soup.find("select", {"name": "list1"}).find_all("option")
    id = set(value.get("value") for value in options)
    id.remove(None)
    return id


# //Step B1
def getBaseData(playerID):
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
            ["injuryStatus", getInjuryStatus(getPlayerUrlFuDa(playerID, data[0][1]))]
        )
    except:
        data.append(["injuryStatus", None])

    # //Add club rank
    try:
        dict = getClubRank()
        rank = dict.get(data[2][1])
        data.append(["clubRank", rank])
    except:
        data.append(["clubRank", None])

    # //Add nomination count of Dreamteam and FavoriteTeam
    # ///Dreamteam
    try:
        dict = getPlayerDataStaCo(playerID)
        data.append(["CountDreTeam", dict.get("dreTeam")])
    except:
        data.append(["CountDreTeam", None])
    # ///FavoriteTeam
    try:
        dict = getPlayerDataStaCo(playerID)
        data.append(["CountFavTeam", dict.get("favTeam")])
    except:
        data.append(["CountFavTeam", None])

    # //Translate data into dictionary
    dictionary = {i[0]: i[-1] for i in data}

    saveDataToFactCsv(dictionary)
    time.sleep(10)


# //Step B2
def saveDataToFactCsv(dataset):
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
    with open(factPlayerCSV, "a") as file:
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
def getMultipleFactData():
    MAX_THREADS = 10  # //higher number increases processing speed
    playerIDs = getPlayerIDs()
    threads = min(MAX_THREADS, len(playerIDs))

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(getBaseData, playerIDs)


# //Step C1
def getPlayerUrlFuDa(playerID, name):
    # //Based on Data from Fussballdaten.de
    mainUrl = "https://classic.comunio.de/bundesligaspieler/"
    url = mainUrl + str(playerID) + "-" + name + ".html"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    urlList = soup.find(class_="contenttext")

    urls = []
    for url in urlList.find_all("a", href=True, text=re.compile("Fussballdaten.de")):
        urls.append(url["href"])

    return urls[0]


# //Step C1*
def getPlayerDataStaCo(playerID):
    # //Based on Data from Stats.Comunio.de
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


# // Step C2
def getInjuryStatus(link):
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


# // Step D1
def getClubUrlFuDa(link):
    playerUrl = link
    page = requests.get(playerUrl)
    soup = BeautifulSoup(page.content, "html.parser")
    step1 = soup.find(class_="box person")
    step2 = step1.find("a", href=True)
    urlPrefix = step2["href"]
    url = "https://www.fussballdaten.de/" + urlPrefix
    return url


# // Step D2
def getClubRank():
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


# //Final Step
def mainFunc():
    t0 = time.time()

    print("++++ Update Data & write to fact_Player.csv ++++")
    getMultipleFactData()
    t1 = time.time()
    print("++++ Load done!" + f"Load took {round(t1 - t0, 2)} seconds ++++")
