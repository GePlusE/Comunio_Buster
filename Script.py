import Player_Class
import Process_Class
import time
import PyDrive_Modul as PYD


def main():
    ############## Settings ##############
    data_file = "fact_Player2.csv"
    log_file = ""
    ######################################

    t0 = time.time()

    Process = Process_Class.Process()
    club_ranks = Process.club_table_dict
    ID_set = Process.player_ID_set
    Process.sequential_load(ID_set)

    PYD.download_file(data_file)

    Process.write_to_csv(Process.dataset, data_file)

    PYD.update_file(data_file)
    t1 = time.time()
    print(f": Duration: {round(t1 - t0, 2)} seconds.")

