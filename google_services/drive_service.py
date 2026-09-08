from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from google_services.auth import get_credentials


def get_drive_service():
    """
    Create and return Google Drive API service.
    """

    creds = get_credentials()

    return build(
        "drive",
        "v3",
        credentials=creds
    )


def upload_file_to_drive(
    file_path,
    file_name,
    folder_id=None
):
    """
    Upload a file to Google Drive.

    Returns:
        Dictionary containing:
        - id
        - name
        - webViewLink
    """

    service = get_drive_service()

    file_metadata = {
        "name": file_name
    }

    # If a Google Drive folder ID is provided,
    # upload the file inside that folder.
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaFileUpload(
        file_path,
        resumable=True
    )

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name, webViewLink"
    ).execute()

    print(
        f"✅ Uploaded to Google Drive: "
        f"{uploaded_file['name']}"
    )

    print(
        f"🔗 Drive Link: "
        f"{uploaded_file.get('webViewLink')}"
    )

    return uploaded_file


# ---------------------------------------------------------
# Test
# ---------------------------------------------------------

if __name__ == "__main__":

    result = upload_file_to_drive(
        file_path="uploads/test.xlsx",
        file_name="test.xlsx"
    )

    print("\nUpload Result:")
    print(result)