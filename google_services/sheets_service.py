from googleapiclient.discovery import build
from google_services.auth import get_credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]


SPREADSHEET_ID = "1xcYpwtU-V8x8nr81rUfiVz1dH5LxMp-mYZzqVTViCpU"


def get_service():
    """
    Create and return Google Sheets API service.
    """

    creds = get_credentials()

    return build(
        "sheets",
        "v4",
        credentials=creds
    )


def save_student_result(
    student_name,
    email,
    attendance_number,
    grade,
    project_id,
    score,
    max_score,
    status,
    feedback
):
    """
    Save the final student grading result to Google Sheets.

    Columns:

    A = Student Name
    B = Email
    C = Attendance Number
    D = Grade
    E = Project ID
    F = Score
    G = Max Score
    H = Status
    I = Feedback

    The score is calculated by the grading engine.
    AI feedback does not calculate or modify the score.
    """

    service = get_service()

    # Make sure all values are safe for Google Sheets
    student_name = str(student_name).strip()
    email = str(email).strip().lower()
    attendance_number = str(attendance_number).strip()
    grade = str(grade).strip().upper()
    project_id = str(project_id).strip()

    if not isinstance(feedback, str):
        feedback = str(feedback)

    feedback = feedback.strip()

    row = [
        student_name,
        email,
        attendance_number,
        grade,
        project_id,
        score,
        max_score,
        status,
        feedback
    ]

    body = {
        "values": [row]
    }

    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet1!A:I",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()

    print(
        f"✅ Saved student result | "
        f"Name: {student_name} | "
        f"Attendance: {attendance_number} | "
        f"Grade: {grade} | "
        f"Project: {project_id} | "
        f"Score: {score}/{max_score}"
    )


def email_exists(email):
    """
    Check whether an email already exists in Google Sheets.

    Email is stored in column B.
    Returns:
        True  -> email already exists
        False -> email does not exist
    """

    service = get_service()

    email = str(email).strip().lower()

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet1!B:B"
    ).execute()

    values = result.get("values", [])

    for row in values:
        if row:
            existing_email = str(row[0]).strip().lower()

            if existing_email == email:
                return True

    return False



# ---------------------------------------------------------
# Test
# ---------------------------------------------------------

if __name__ == "__main__":

    save_student_result(
        student_name="Ali",
        email="ali@example.com",
        attendance_number="01",
        grade="10A",
        project_id="project_1",
        score=16,
        max_score=20,
        status="PASSED",
        feedback="The project was graded successfully."
    )
