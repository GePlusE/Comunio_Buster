import Player_Class
import Process_Class
import time
import PyDrive_Modul as PYD


############## Settings ##############
data_file = "fact_Player2.csv"
creds_file = "mycreds.json"
######################################


def main():
    # starting the whole Scrapping Script
    t0 = time.time()

    # Downloading
    PYD.download_file(data_file)
    PYD.download_file(creds_file)

    # Process
    Process = Process_Class.Process()
    club_ranks = Process.club_table_dict
    ID_set = Process.player_ID_set
    Process.sequential_load(ID_set)
    Process.write_to_csv(Process.dataset, data_file)

    # Uploading
    PYD.update_file(data_file)
    PYD.update_file(creds_file)

    t1 = time.time()
    print(f": Duration: {round(t1 - t0, 2)} seconds.")

