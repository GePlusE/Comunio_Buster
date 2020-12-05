from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


def google_drive_auth():
    gauth = GoogleAuth()
    # Try to load saved client credentials
    gauth.LoadCredentialsFile("mycreds.json")
    if gauth.credentials is None:
        # Authenticate if they're not there
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved creds
        gauth.Authorize()
    # Save the current credentials to a file
    gauth.SaveCredentialsFile("mycreds.json")

    drive = GoogleDrive(gauth)
    return drive


def upload_file_to_folder(filename, folder_ID="1-IBreIAcF-oAwnLcoNKxtAbEMAp0Cr07"):
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


def get_ID_of_title(
    title, parent_directory_ID="1-IBreIAcF-oAwnLcoNKxtAbEMAp0Cr07"
):  # "1-IBreIAcF-oAwnLcoNKxtAbEMAp0Cr07" is the Comunio_Buster folderID
    # authenticate
    drive = google_drive_auth()
    foldered_list = drive.ListFile(
        {"q": "'" + parent_directory_ID + "' in parents and trashed=false"}
    ).GetList()
    for file in foldered_list:
        if file["title"] == title:
            return file["id"]
    return None


def download_file(filename):  # , folder_ID="1-IBreIAcF-oAwnLcoNKxtAbEMAp0Cr07"):
    file_ID = get_ID_of_title(filename)
    drive = google_drive_auth()
    file1 = drive.CreateFile({"id": file_ID})  # , "q": folder_ID})
    file1.GetContentFile(file1["title"])


def update_file(filename, folder_ID="1-IBreIAcF-oAwnLcoNKxtAbEMAp0Cr07"):
    file_ID = get_ID_of_title(filename)
    # if file does not exist upload_file is used
    if file_ID is None:
        upload_file_to_folder(filename)
        print("Upload")
    # update file based on file_ID
    else:
        print("Update")
        # authenticate
        drive = google_drive_auth()
        # upload file with given name
        upload_file = drive.CreateFile({"parents": [{"id": folder_ID}], "id": file_ID})
        upload_file.SetContentFile(filename)
        upload_file.Upload()


# print(get_ID_of_title("fact_Player2.csv"))
# download_file("fact_Player2.csv")
