import requests
import urllib.request
import logging
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


def check_url_status(url, function_name=None):
    # Check url status & log if status is not 200
    try:
        url_status = urllib.request.urlopen(url).getcode()
        if url_status > 299:
            logging.warning(f"{url} showed status code {url_status}")
    except:
        logging.warning(f"check_url_status failed in {function_name} for {url}")

