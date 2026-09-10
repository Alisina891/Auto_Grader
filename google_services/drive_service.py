import io
import re

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

from google_services.auth import get_credentials


# ============================================================
# DRIVE SERVICE
# ============================================================

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


# ============================================================
# NAME HELPERS
# ============================================================

def safe_name(value):
    """
    Make a value safe to use as a Google Drive
    file/folder name.
    """

    value = str(value).strip()

    if not value:
        return "Unknown"

    value = re.sub(r'[\\/:*?"<>|]', "_", value)

    return value


# ============================================================
# FIND FILE / FOLDER
# ============================================================

def find_item(name, parent_id=None, mime_type=None):
    """
    Find a file or folder by exact name.

    Returns:
        File dictionary or None
    """

    service = get_drive_service()

    name = safe_name(name)

    query_parts = [
        f"name = '{name.replace(chr(39), chr(92) + chr(39))}'",
        "trashed = false"
    ]

    if parent_id:
        query_parts.append(
            f"'{parent_id}' in parents"
        )

    if mime_type:
        query_parts.append(
            f"mimeType = '{mime_type}'"
        )

    query = " and ".join(query_parts)

    result = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name, mimeType, parents, webViewLink)",
        pageSize=10
    ).execute()

    files = result.get("files", [])

    if files:
        return files[0]

    return None


# ============================================================
# CREATE FOLDER
# ============================================================

def create_folder(folder_name, parent_id=None):
    """
    Create a Google Drive folder.

    If the folder already exists, return the existing folder.
    """

    service = get_drive_service()

    folder_name = safe_name(folder_name)

    existing = find_item(
        name=folder_name,
        parent_id=parent_id,
        mime_type="application/vnd.google-apps.folder"
    )

    if existing:
        return existing

    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder"
    }

    if parent_id:
        metadata["parents"] = [parent_id]

    folder = service.files().create(
        body=metadata,
        fields="id, name, mimeType, parents, webViewLink"
    ).execute()

    print(
        f"📁 Created Google Drive folder: "
        f"{folder['name']}"
    )

    return folder


# ============================================================
# GET PROJECT FOLDERS
# ============================================================

def get_master_project_folder(project_id):
    """
    Get:

        Auto_Grader
            └── Master_Projects
                └── Project_X
    """

    root = create_folder("Auto_Grader")

    master_projects = create_folder(
        "Master_Projects",
        parent_id=root["id"]
    )

    project_folder = create_folder(
        f"Project_{safe_name(project_id)}",
        parent_id=master_projects["id"]
    )

    return project_folder


def get_student_project_folder(project_id):
    """
    Get:

        Auto_Grader
            └── Student_Projects
                └── Project_X
    """

    root = create_folder("Auto_Grader")

    student_projects = create_folder(
        "Student_Projects",
        parent_id=root["id"]
    )

    project_folder = create_folder(
        f"Project_{safe_name(project_id)}",
        parent_id=student_projects["id"]
    )

    return project_folder


def get_student_grade_folder(project_id, grade):
    """
    Get:

        Auto_Grader
            └── Student_Projects
                └── Project_X
                    └── Grade
    """

    project_folder = get_student_project_folder(
        project_id
    )

    grade_folder = create_folder(
        safe_name(grade).upper(),
        parent_id=project_folder["id"]
    )

    return grade_folder


# ============================================================
# UPLOAD FILE
# ============================================================

def upload_file_to_drive(
    file_path,
    file_name,
    folder_id=None
):
    """
    Upload a local file to Google Drive.

    Returns:
        Dictionary containing:
            id
            name
            webViewLink
    """

    service = get_drive_service()

    file_name = safe_name(file_name)

    file_metadata = {
        "name": file_name
    }

    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaFileUpload(
        file_path,
        resumable=True
    )

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name, webViewLink, parents"
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


# ============================================================
# UPLOAD JSON DIRECTLY TO DRIVE
# ============================================================

def upload_json_to_drive(
    data,
    file_name,
    folder_id=None
):
    """
    Upload JSON data directly to Google Drive.

    No temporary JSON file is created on Render.
    """

    import json

    service = get_drive_service()

    file_name = safe_name(file_name)

    json_data = json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    )

    media = MediaIoBaseUpload(
        io.BytesIO(
            json_data.encode("utf-8")
        ),
        mimetype="application/json",
        resumable=True
    )

    existing = find_item(
        name=file_name,
        parent_id=folder_id
    )

    file_metadata = {
        "name": file_name
    }

    if folder_id:
        file_metadata["parents"] = [folder_id]

    if existing:

        uploaded_file = service.files().update(
            fileId=existing["id"],
            media_body=media,
            fields="id, name, webViewLink, parents"
        ).execute()

        print(
            f"🔄 Updated Google Drive JSON: "
            f"{file_name}"
        )

    else:

        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink, parents"
        ).execute()

        print(
            f"✅ Uploaded Google Drive JSON: "
            f"{file_name}"
        )

    return uploaded_file


# ============================================================
# DOWNLOAD JSON FROM DRIVE
# ============================================================

def download_json_from_drive(
    file_name,
    folder_id=None
):
    """
    Read a JSON file directly from Google Drive.

    Returns:
        Python dictionary
        or None if the file does not exist.
    """

    import json

    service = get_drive_service()

    file_info = find_item(
        name=file_name,
        parent_id=folder_id
    )

    if not file_info:
        print(
            f"⚠️ Google Drive JSON not found: "
            f"{file_name}"
        )
        return None

    content = service.files().get(
        fileId=file_info["id"],
        alt="media"
    ).execute()

    if isinstance(content, bytes):
        content = content.decode("utf-8")

    if isinstance(content, dict):
        data = content
    else:
        data = json.loads(content)

    print(
        f"✅ Loaded JSON from Google Drive: "
        f"{file_name}"
    )

    return data


# ============================================================
# DELETE FILE
# ============================================================

def delete_file_from_drive(file_id):
    """
    Delete a file from Google Drive.
    """

    service = get_drive_service()

    service.files().delete(
        fileId=file_id
    ).execute()

    print(
        f"🗑️ Deleted Google Drive file: "
        f"{file_id}"
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    folder = get_master_project_folder(1)

    print("\nMaster Project Folder:")
    print(folder)