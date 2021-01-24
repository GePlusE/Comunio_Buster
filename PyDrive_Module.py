import logging

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


############################ Logging Settings ############################
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s %(levelname)s: %(filename)s: %(message)s")
# get formats from https://docs.python.org/3/library/logging.html#logrecord-attributes

file_handler = logging.FileHandler("LogFile.log")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
##########################################################################

# You can find the FolderID in the URL of the folder
PROD = "1-IBreIAcF-oAwnLcoNKxtAbEMAp0Cr07"
DEV = "1RI058Dqli3EbOuyrW0PWHVCl8H5hdPWX"

folder_in_use = PROD

creds_file = "mycreds.json"


def google_drive_auth():
    # get auth from Google Drive
    try:
        gauth = GoogleAuth()
        # Try to load saved client credentials
        gauth.LoadCredentialsFile(creds_file)
        if gauth.credentials is None:
            # Authenticate if they're not there
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            # Refresh token if expired
            gauth.Refresh()
        else:
            # Initialize the saved creds
            gauth.Authorize()
        # Save the current credentials to a file
        gauth.SaveCredentialsFile(creds_file)

        drive = GoogleDrive(gauth)
        return drive
    except:
        logger.exception(f"Could not authenticate with Google Drive.")
        pass


def upload_file_to_folder(filename, folder_ID=folder_in_use):
    # Upload file to given folder
    try:
        # authenticate
        drive = google_drive_auth()
        # upload file with given name
        upload_file = drive.CreateFile({"parents": [{"id": folder_ID}]})
        upload_file.SetContentFile(filename)
        upload_file.Upload()
    except:
        logger.info(f"Could not upload {filename}.")
        pass


def list_files():
    # authenticate
    drive = google_drive_auth()
    # search al files with given specs
    file_list = drive.ListFile({"q": "'root' in parents and trashed=false"}).GetList()
    for file1 in file_list:
        print("title: %s, id: %s" % (file1["title"], file1["id"]))


def get_ID_of_title(title, parent_directory_ID=folder_in_use):
    # get fileID from given file title in specific folder
    try:
        # authenticate
        drive = google_drive_auth()
        foldered_list = drive.ListFile(
            {"q": "'" + parent_directory_ID + "' in parents and trashed=false"}
        ).GetList()
        for file in foldered_list:
            if file["title"] == title:
                return file["id"]
        return None
    except:
        logger.exception(f"Could not get fileID of {title}.")
        pass


def download_file(filename):
    # downloading file by filename
    try:
        file_ID = get_ID_of_title(filename)
        drive = google_drive_auth()
        file1 = drive.CreateFile({"id": file_ID})  # , "q": folder_ID})
        file1.GetContentFile(file1["title"])
    except:
        logger.exception(f"Could not download {filename}.")
        pass


def update_file(filename, folder_ID=folder_in_use):
    # Update given file in given folder
    try:
        file_ID = get_ID_of_title(filename)
        # if file does not exist upload_file is used
        if file_ID is None:
            upload_file_to_folder(filename)
        # update file based on file_ID
        else:
            # authenticate
            drive = google_drive_auth()
            # upload file with given name
            upload_file = drive.CreateFile(
                {"parents": [{"id": folder_ID}], "id": file_ID}
            )
            upload_file.SetContentFile(filename)
            upload_file.Upload()
    except:
        logger.exception(f"Could not update {filename}.")
        pass


if __name__ == "__main__":
    pass

