import re

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

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
        credentials=creds,
    )


# ============================================================
# HELPERS
# ============================================================

def safe_name(value):
    """
    Make a value safe for Google Drive file/folder names.
    """

    value = str(value).strip()

    if not value:
        return "Unknown"

    return re.sub(
        r'[\\/:*?"<>|]',
        "_",
        value,
    )


# ============================================================
# FIND ITEM
# ============================================================

def find_item(
    name,
    parent_id=None,
    mime_type=None,
):
    """
    Find an exact file/folder by name.

    Returns:
        dict | None
    """

    service = get_drive_service()

    name = safe_name(name)

    escaped_name = name.replace(
        "'",
        "\\'",
    )

    query_parts = [
        f"name = '{escaped_name}'",
        "trashed = false",
    ]

    if parent_id:
        query_parts.append(
            f"'{parent_id}' in parents"
        )

    if mime_type:
        query_parts.append(
            f"mimeType = '{mime_type}'"
        )

    query = " and ".join(
        query_parts
    )

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
        pageSize=10,
    ).execute()

    files = result.get(
        "files",
        [],
    )

    if files:
        return files[0]

    return None


# ============================================================
# CREATE FOLDER
# ============================================================

def create_folder(
    folder_name,
    parent_id=None,
):
    """
    Create a folder if it does not already exist.

    Returns the existing/new folder.
    """

    service = get_drive_service()

    folder_name = safe_name(
        folder_name
    )

    existing = find_item(
        name=folder_name,
        parent_id=parent_id,
        mime_type="application/vnd.google-apps.folder",
    )

    if existing:
        return existing

    metadata = {
        "name": folder_name,
        "mimeType": (
            "application/vnd.google-apps.folder"
        ),
    }

    if parent_id:
        metadata["parents"] = [
            parent_id
        ]

    folder = service.files().create(
        body=metadata,
        fields=(
            "id,"
            "name,"
            "mimeType,"
            "parents,"
            "webViewLink"
        ),
    ).execute()

    print(
        f"📁 Created Google Drive folder: "
        f"{folder['name']}"
    )

    return folder


# ============================================================
# AUTO GRADER ROOT
# ============================================================

def get_autograder_root_folder():
    """
    Get:

        Auto_Grader/
    """

    return create_folder(
        "Auto_Grader"
    )


# ============================================================
# TYPE ROOT
# ============================================================

def get_type_root_folder(
    file_type="excel",
):
    """
    Get the separate root for Excel or Word.

    Structure:

        Auto_Grader/
            Excel/

    or:

        Auto_Grader/
            Word/
    """

    file_type = str(
        file_type
    ).strip().lower()

    if file_type not in {
        "excel",
        "word",
    }:

        raise ValueError(
            "file_type must be 'excel' or 'word'"
        )

    root = get_autograder_root_folder()

    return create_folder(
        file_type.capitalize(),
        parent_id=root["id"],
    )


# ============================================================
# STUDENT ROOT
# ============================================================

def get_student_root_folder(
    file_type="excel",
):
    """
    Get:

        Auto_Grader/
            Excel/
                Student_Projects/

    or:

        Auto_Grader/
            Word/
                Student_Projects/
    """

    type_root = get_type_root_folder(
        file_type
    )

    return create_folder(
        "Student_Projects",
        parent_id=type_root["id"],
    )


# ============================================================
# STUDENT PROJECT FOLDER
# ============================================================

def get_student_project_folder(
    project_id,
    file_type="excel",
):
    """
    Get:

        Auto_Grader/
            Excel/
                Student_Projects/
                    Project_X/

    or:

        Auto_Grader/
            Word/
                Student_Projects/
                    Project_X/
    """

    student_root = get_student_root_folder(
        file_type
    )

    project_folder = create_folder(
        f"Project_{safe_name(project_id)}",
        parent_id=student_root["id"],
    )

    return project_folder


# ============================================================
# STUDENT GRADE FOLDER
# ============================================================

def get_student_grade_folder(
    project_id,
    grade,
    file_type="excel",
):
    """
    Get:

        Auto_Grader/
            Excel/
                Student_Projects/
                    Project_X/
                        10A/

    or:

        Auto_Grader/
            Word/
                Student_Projects/
                    Project_X/
                        10A/
    """

    project_folder = get_student_project_folder(
        project_id,
        file_type=file_type,
    )

    grade_folder = create_folder(
        safe_name(grade).upper(),
        parent_id=project_folder["id"],
    )

    return grade_folder


# ============================================================
# UPLOAD STUDENT FILE
# ============================================================

def upload_file_to_drive(
    file_path,
    file_name,
    folder_id=None,
):
    """
    Upload a student file to Google Drive.

    This function is used for student Excel/Word files.
    """

    service = get_drive_service()

    file_name = safe_name(
        file_name
    )

    metadata = {
        "name": file_name,
    }

    if folder_id:
        metadata["parents"] = [
            folder_id
        ]

    media = MediaFileUpload(
        file_path,
        resumable=True,
    )

    uploaded_file = service.files().create(
        body=metadata,
        media_body=media,
        fields=(
            "id,"
            "name,"
            "mimeType,"
            "size,"
            "webViewLink,"
            "parents"
        ),
    ).execute()

    print()
    print("========================================")
    print("✅ GOOGLE DRIVE FILE UPLOADED")
    print("Name:", uploaded_file.get("name"))
    print("ID:", uploaded_file.get("id"))
    print("Folder:", uploaded_file.get("parents"))
    print("Link:", uploaded_file.get("webViewLink"))
    print("========================================")
    print()

    return uploaded_file


# ============================================================
# DELETE FILE
# ============================================================

def delete_file_from_drive(
    file_id,
):
    """
    Permanently delete a Drive file.
    """

    service = get_drive_service()

    service.files().delete(
        fileId=file_id
    ).execute()

    print(
        f"🗑️ Deleted Google Drive file: "
        f"{file_id}"
    )