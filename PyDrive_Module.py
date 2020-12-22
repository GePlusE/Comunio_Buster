from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# TODO: Add Logging to all functions with Tracebacks
# TODO: Check if try-statements are necessary

folder_in_use = "1-IBreIAcF-oAwnLcoNKxtAbEMAp0Cr07"
# You can find the FolderID in the URL of the folder
# FolderID PROD = "1-IBreIAcF-oAwnLcoNKxtAbEMAp0Cr07"
# FolderID DEV = "1RI058Dqli3EbOuyrW0PWHVCl8H5hdPWX"


def google_drive_auth():
    gauth = GoogleAuth()
    # Try to load saved client credentials
    gauth.LoadCredentialsFile("mycreds.json")
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
    gauth.SaveCredentialsFile("mycreds.json")

    drive = GoogleDrive(gauth)
    return drive


def upload_file_to_folder(filename, folder_ID=folder_in_use):
    # authenticate
    drive = google_drive_auth()
    # upload file with given name
    upload_file = drive.CreateFile({"parents": [{"id": folder_ID}]})
    upload_file.SetContentFile(filename)
    upload_file.Upload()


def list_files():
    # authenticate
    drive = google_drive_auth()
    # search al files with given specs
    file_list = drive.ListFile({"q": "'root' in parents and trashed=false"}).GetList()
    for file1 in file_list:
        print("title: %s, id: %s" % (file1["title"], file1["id"]))


def get_ID_of_title(title, parent_directory_ID=folder_in_use):
    # authenticate
    drive = google_drive_auth()
    foldered_list = drive.ListFile(
        {"q": "'" + parent_directory_ID + "' in parents and trashed=false"}
    ).GetList()
    for file in foldered_list:
        if file["title"] == title:
            return file["id"]
    return None


def download_file(filename):
    file_ID = get_ID_of_title(filename)
    drive = google_drive_auth()
    file1 = drive.CreateFile({"id": file_ID})  # , "q": folder_ID})
    file1.GetContentFile(file1["title"])


def update_file(filename, folder_ID=folder_in_use):
    file_ID = get_ID_of_title(filename)
    # if file does not exist upload_file is used
    if file_ID is None:
        upload_file_to_folder(filename)
    # update file based on file_ID
    else:
        # authenticate
        drive = google_drive_auth()
        # upload file with given name
        upload_file = drive.CreateFile({"parents": [{"id": folder_ID}], "id": file_ID})
        upload_file.SetContentFile(filename)
        upload_file.Upload()


if __name__ == "__main__":
    pass

