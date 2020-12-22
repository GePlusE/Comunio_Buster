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


folder_in_use = "1RI058Dqli3EbOuyrW0PWHVCl8H5hdPWX"
# You can find the FolderID in the URL of the folder
# FolderID PROD = "1-IBreIAcF-oAwnLcoNKxtAbEMAp0Cr07"
# FolderID DEV = "1RI058Dqli3EbOuyrW0PWHVCl8H5hdPWX"
creds_file = "mycreds.json"


def google_drive_auth():
    try:
        gauth = GoogleAuth()
        # Try to load saved client credentials
        gauth.LoadCredentialsFile(creds_file)
        if gauth.credentials is None:
            # Authenticate if they're not there
            gauth.LocalWebserverAuth()
            logger.info(f"Missing {creds_file} -> new authentication")
        elif gauth.access_token_expired:
            # Refresh token if expired
            gauth.Refresh()
            logger.info(f"refreshed expired token")
        else:
            # Initialize the saved creds
            gauth.Authorize()
        # Save the current credentials to a file
        gauth.SaveCredentialsFile(creds_file)
        drive = GoogleDrive(gauth)
        return drive
    except:
        logger.exception(f"google_drive_auth failed")
        raise


def upload_file_to_folder(filename, folder_ID=folder_in_use):
    try:
        # authenticate
        drive = google_drive_auth()
        # upload file with given name
        upload_file = drive.CreateFile({"parents": [{"id": folder_ID}]})
        upload_file.SetContentFile(filename)
        upload_file.Upload()
        # Logging
        logger.info(f"Upload: {filename}")
    except:
        logger.exception(f"upload_file_to_folder failed")
        raise


def list_files():
    # authenticate
    drive = google_drive_auth()
    # search al files with given specs
    file_list = drive.ListFile({"q": "'root' in parents and trashed=false"}).GetList()
    for file1 in file_list:
        print("title: %s, id: %s" % (file1["title"], file1["id"]))


def get_ID_of_title(title, parent_directory_ID=folder_in_use):
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
        logger.exception(f"get_ID_of_title failed")
        raise


def download_file(filename):
    try:
        # downloading given file
        file_ID = get_ID_of_title(filename)
        drive = google_drive_auth()
        file1 = drive.CreateFile({"id": file_ID})  # , "q": folder_ID})
        file1.GetContentFile(file1["title"])
        # logging
        logger.info(f"Download: {filename}")
    except:
        logger.exception(f"download_file failed")
        raise


def update_file(filename, folder_ID=folder_in_use):
    try:
        # update existing file
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

            # logging
            logger.info(f"Update: {filename}")
    except:
        logger.exception(f"update_file failed")
        raise


if __name__ == "__main__":
    pass

