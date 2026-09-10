import io
import re
import json

from googleapiclient.discovery import build
from googleapiclient.http import (
    MediaFileUpload,
    MediaIoBaseUpload
)
from google.auth.transport.requests import AuthorizedSession

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

    escaped_name = name.replace(
        "'",
        "\\'"
    )

    query_parts = [
        f"name = '{escaped_name}'",
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
        fields=(
            "files("
            "id,"
            "name,"
            "mimeType,"
            "parents,"
            "size,"
            "modifiedTime,"
            "webViewLink"
            ")"
        ),
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

    If the folder already exists, return it.
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
        fields="id,name,mimeType,parents,webViewLink"
    ).execute()

    print(
        f"📁 Created Google Drive folder: "
        f"{folder['name']}"
    )

    return folder


# ============================================================
# GET MASTER PROJECT FOLDER
# ============================================================

def get_master_project_folder(project_id):
    """
    Get:

        Auto_Grader
            └── Master_Projects
                └── Project_X
    """

    root = create_folder(
        "Auto_Grader"
    )

    master_projects = create_folder(
        "Master_Projects",
        parent_id=root["id"]
    )

    project_folder = create_folder(
        f"Project_{safe_name(project_id)}",
        parent_id=master_projects["id"]
    )

    return project_folder


# ============================================================
# GET STUDENT PROJECT FOLDER
# ============================================================

def get_student_project_folder(project_id):
    """
    Get:

        Auto_Grader
            └── Student_Projects
                └── Project_X
    """

    root = create_folder(
        "Auto_Grader"
    )

    student_projects = create_folder(
        "Student_Projects",
        parent_id=root["id"]
    )

    project_folder = create_folder(
        f"Project_{safe_name(project_id)}",
        parent_id=student_projects["id"]
    )

    return project_folder


# ============================================================
# GET STUDENT GRADE FOLDER
# ============================================================

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
        fields="id,name,mimeType,size,webViewLink,parents"
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
# UPLOAD JSON TO DRIVE
# ============================================================

def upload_json_to_drive(
    data,
    file_name,
    folder_id=None
):
    """
    Upload or update JSON data in Google Drive.
    """

    service = get_drive_service()

    file_name = safe_name(file_name)

    json_data = json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    )

    json_bytes = json_data.encode("utf-8")

    print()
    print("========== SAVING JSON TO DRIVE ==========")
    print("FILE:", file_name)
    print("FOLDER:", folder_id)
    print("JSON SIZE:", len(json_bytes))
    print("==========================================")

    media = MediaIoBaseUpload(
        io.BytesIO(json_bytes),
        mimetype="application/json",
        resumable=False
    )

    existing = find_item(
        name=file_name,
        parent_id=folder_id,
        mime_type="application/json"
    )

    if existing:

        print(
            f"🔄 Updating existing JSON file: "
            f"{existing['id']}"
        )

        uploaded_file = service.files().update(
            fileId=existing["id"],
            body={
                "name": file_name,
                "mimeType": "application/json"
            },
            media_body=media,
            fields=(
                "id,"
                "name,"
                "mimeType,"
                "size,"
                "parents,"
                "webViewLink"
            )
        ).execute()

    else:

        print("➕ Creating new JSON file")

        file_metadata = {
            "name": file_name,
            "mimeType": "application/json"
        }

        if folder_id:
            file_metadata["parents"] = [folder_id]

        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields=(
                "id,"
                "name,"
                "mimeType,"
                "size,"
                "parents,"
                "webViewLink"
            )
        ).execute()

    print()
    print("========== DRIVE JSON SAVED ==========")
    print("ID:", uploaded_file.get("id"))
    print("NAME:", uploaded_file.get("name"))
    print("MIME:", uploaded_file.get("mimeType"))
    print("SIZE:", uploaded_file.get("size"))
    print("======================================")

    return uploaded_file


# ============================================================
# DOWNLOAD JSON CONTENT
# ============================================================

def download_json_from_drive(
    file_name,
    folder_id=None
):
    """
    Download actual JSON content from Google Drive.

    This uses an authenticated HTTP session instead of
    googleapiclient's media execute() because the latter was
    returning Drive metadata in this project.
    """

    file_name = safe_name(file_name)

    print()
    print("==========================================")
    print("📥 DOWNLOADING JSON FROM GOOGLE DRIVE")
    print("FILE:", file_name)
    print("FOLDER:", folder_id)
    print("==========================================")

    # --------------------------------------------------------
    # FIND FILE
    # --------------------------------------------------------

    file_info = find_item(
        name=file_name,
        parent_id=folder_id,
        mime_type="application/json"
    )

    if not file_info:

        print(
            f"⚠️ Google Drive JSON not found: "
            f"{file_name}"
        )

        return None

    file_id = file_info["id"]

    print("FILE ID:", file_id)
    print("FILE NAME:", file_info.get("name"))
    print("FILE MIME:", file_info.get("mimeType"))
    print("FILE SIZE:", file_info.get("size"))
    print("FILE PARENTS:", file_info.get("parents"))

    # --------------------------------------------------------
    # GET CREDENTIALS
    # --------------------------------------------------------

    creds = get_credentials()

    # --------------------------------------------------------
    # AUTHENTICATED SESSION
    # --------------------------------------------------------

    session = AuthorizedSession(
        creds
    )

    url = (
        "https://www.googleapis.com/drive/v3/files/"
        + file_id
    )

    print()
    print("REQUEST URL:")
    print(url)

    # --------------------------------------------------------
    # DOWNLOAD ACTUAL FILE CONTENT
    # --------------------------------------------------------

    response = session.get(
        url,
        params={
            "alt": "media"
        }
    )

    print()
    print("========== DRIVE RESPONSE ==========")
    print("STATUS:", response.status_code)
    print("CONTENT TYPE:", response.headers.get("content-type"))
    print("CONTENT LENGTH:", len(response.content))
    print("====================================")

    if response.status_code != 200:

        print(
            "❌ Google Drive download failed."
        )

        print(
            "RESPONSE:",
            response.text[:1000]
        )

        return None

    content = response.content

    # --------------------------------------------------------
    # DEBUG RAW CONTENT
    # --------------------------------------------------------

    print()
    print("========== RAW JSON DOWNLOAD ==========")
    print(
        content[:500].decode(
            "utf-8",
            errors="replace"
        )
    )
    print("========================================")

    # --------------------------------------------------------
    # DECODE UTF-8
    # --------------------------------------------------------

    try:

        text = content.decode(
            "utf-8"
        )

    except UnicodeDecodeError as e:

        print(
            f"❌ UTF-8 decoding failed: {e}"
        )

        return None

    # --------------------------------------------------------
    # PARSE JSON
    # --------------------------------------------------------

    try:

        data = json.loads(
            text
        )

    except json.JSONDecodeError as e:

        print()
        print(
            f"❌ JSON parsing failed: {e}"
        )

        print(
            "CONTENT:",
            text[:1000]
        )

        return None

    # --------------------------------------------------------
    # VERIFY DICTIONARY
    # --------------------------------------------------------

    if not isinstance(data, dict):

        print(
            "❌ Downloaded JSON is not a dictionary."
        )

        print(
            "TYPE:",
            type(data)
        )

        return None

    # --------------------------------------------------------
    # VERIFY MASTER RULE STRUCTURE
    # --------------------------------------------------------

    required_keys = [
        "file_name",
        "total_sheets",
        "sheet_names",
        "sheets"
    ]

    missing = [
        key
        for key in required_keys
        if key not in data
    ]

    if missing:

        print()
        print("❌ INVALID MASTER RULES")
        print("Missing:", missing)
        print("Actual keys:", list(data.keys()))
        print()

        # This is useful for catching the old problem.
        if set(data.keys()) == {
            "kind",
            "id",
            "name",
            "mimeType"
        }:

            print(
                "⚠️ WARNING:"
            )

            print(
                "Google Drive metadata was returned "
                "instead of JSON content."
            )

        return None

    # --------------------------------------------------------
    # VERIFY SHEETS
    # --------------------------------------------------------

    if not isinstance(
        data.get("sheets"),
        dict
    ):

        print(
            "❌ Invalid 'sheets' structure."
        )

        return None

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    print()
    print("========== MASTER RULES LOADED ==========")
    print(
        "FILE:",
        data.get("file_name")
    )
    print(
        "TOTAL SHEETS:",
        data.get("total_sheets")
    )
    print(
        "SHEET NAMES:",
        data.get("sheet_names")
    )
    print(
        "SHEETS:",
        list(
            data.get(
                "sheets",
                {}
            ).keys()
        )
    )
    print(
        "JSON SIZE:",
        len(content)
    )
    print("=========================================")

    return data


# ============================================================
# DELETE FILE
# ============================================================

def delete_file_from_drive(file_id):
    """
    Delete a Google Drive file.
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

    print()
    print("Master Project Folder:")
    print(folder)