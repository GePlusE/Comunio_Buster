import Player_Class
import Process_Class
import time
import PyDrive_Module as PYD
import Scrape_Transfermarkt as STM
import logging


############################ Logging Settings ############################
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s %(levelname)s: %(filename)s: %(message)s")
# get formats from https://docs.python.org/3/library/logging.html#logrecord-attributes

file_handler = logging.FileHandler("LogFile.log")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
##########################################################################


############## Settings ##############
data_file = "fact_Player2.csv"
creds_file = "mycreds.json"
log_file = "LogFile.log"
dim_json = "player_dim.json"
######################################


def main():
    # starting the scrapping Script
    t0 = time.time()

    # Downloading
    PYD.download_file(data_file)
    PYD.download_file(creds_file)
    PYD.download_file(log_file)
    PYD.download_file(dim_json)

    logger.info(f"START SCRAPPING & DATA UPDATE")
    # Process
    Process = Process_Class.Process()
    club_ranks = Process.club_table_dict
    ID_set = Process.player_ID_set
    Process.sequential_load(list(ID_set)[:10])
    STM.match_Transfermarkt_data()
    Process.write_to_csv(Process.dataset, data_file)

    # Uploading
    PYD.update_file(data_file)
    PYD.update_file(creds_file)
    PYD.update_file(dim_json)
    logger.info(f"Uploaded: {data_file}, {creds_file}, {dim_json}")

    t1 = time.time()
    logger.info(f"END Duration: {round(t1 - t0, 2):,.2f} seconds")
    PYD.update_file(log_file)
