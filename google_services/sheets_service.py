from googleapiclient.discovery import build

from google_services.auth import get_credentials


# ============================================================
# GOOGLE SHEETS
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


# ============================================================
# SPREADSHEET IDS
# ============================================================

EXCEL_SPREADSHEET_ID = (
    "1xcYpwtU-V8x8nr81rUfiVz1dH5LxMp-mYZzqVTViCpU"
)

WORD_SPREADSHEET_ID = (
    "11U-syWjW4NDYtTcHNTk8b9YFWqjeaKZer3TyZKrcDI8"
)


# ============================================================
# GOOGLE SHEETS SERVICE
# ============================================================

def get_service():
    """
    Create and return Google Sheets API service.
    """

    creds = get_credentials()

    return build(
        "sheets",
        "v4",
        credentials=creds,
    )


# ============================================================
# INTERNAL SAVE FUNCTION
# ============================================================

def _save_result(
    spreadsheet_id,
    student_name,
    email,
    attendance_number,
    grade,
    project_id,
    score,
    max_score,
    status,
    feedback,
):
    """
    Save a grading result into a specific
    Google Spreadsheet.
    """

    service = get_service()

    # --------------------------------------------------------
    # NORMALIZE DATA
    # --------------------------------------------------------

    student_name = str(
        student_name
    ).strip()

    email = str(
        email
    ).strip().lower()

    attendance_number = str(
        attendance_number
    ).strip()

    grade = str(
        grade
    ).strip().upper()

    project_id = str(
        project_id
    ).strip()

    status = str(
        status
    ).strip().upper()

    # --------------------------------------------------------
    # NORMALIZE FEEDBACK
    # --------------------------------------------------------

    if feedback is None:

        feedback = ""

    elif not isinstance(
        feedback,
        str,
    ):

        feedback = str(
            feedback
        )

    feedback = feedback.strip()

    # --------------------------------------------------------
    # BUILD ROW
    # --------------------------------------------------------

    row = [
        student_name,
        email,
        attendance_number,
        grade,
        project_id,
        score,
        max_score,
        status,
        feedback,
    ]

    body = {
        "values": [
            row
        ]
    }

    # --------------------------------------------------------
    # SAVE TO GOOGLE SHEETS
    # --------------------------------------------------------

    service.spreadsheets().values().append(

        spreadsheetId=spreadsheet_id,

        # Uses the first sheet.
        # Does not depend on "Sheet1".

        range="A:I",

        valueInputOption="RAW",

        insertDataOption="INSERT_ROWS",

        body=body,

    ).execute()

    # --------------------------------------------------------
    # LOG
    # --------------------------------------------------------

    print(
        f"✅ Saved student result | "
        f"Name: {student_name} | "
        f"Email: {email} | "
        f"Attendance: {attendance_number} | "
        f"Grade: {grade} | "
        f"Project: {project_id} | "
        f"Score: {score}/{max_score} | "
        f"Status: {status}"
    )


# ============================================================
# SAVE EXCEL STUDENT RESULT
# ============================================================

def save_student_result(
    student_name,
    email,
    attendance_number,
    grade,
    project_id,
    score,
    max_score,
    status,
    feedback,
):
    """
    Save an Excel student grading result.
    """

    _save_result(

        spreadsheet_id=EXCEL_SPREADSHEET_ID,

        student_name=student_name,

        email=email,

        attendance_number=attendance_number,

        grade=grade,

        project_id=project_id,

        score=score,

        max_score=max_score,

        status=status,

        feedback=feedback,
    )


# ============================================================
# SAVE WORD STUDENT RESULT
# ============================================================

def save_word_student_result(
    student_name,
    email,
    attendance_number,
    grade,
    project_id,
    score,
    max_score,
    status,
    feedback,
):
    """
    Save a Word student grading result.
    """

    _save_result(

        spreadsheet_id=WORD_SPREADSHEET_ID,

        student_name=student_name,

        email=email,

        attendance_number=attendance_number,

        grade=grade,

        project_id=project_id,

        score=score,

        max_score=max_score,

        status=status,

        feedback=feedback,
    )


# ============================================================
# CHECK EMAIL
# ============================================================

def email_exists(
    email,
    file_type="excel",
):
    """
    Check whether an email already exists
    in the spreadsheet belonging to the
    specified project type.

    file_type:
        excel
        word
    """

    service = get_service()

    # --------------------------------------------------------
    # NORMALIZE EMAIL
    # --------------------------------------------------------

    email = str(
        email
    ).strip().lower()

    # --------------------------------------------------------
    # NORMALIZE FILE TYPE
    # --------------------------------------------------------

    file_type = str(
        file_type
    ).strip().lower()

    # --------------------------------------------------------
    # SELECT SPREADSHEET
    # --------------------------------------------------------

    if file_type == "excel":

        spreadsheet_id = (
            EXCEL_SPREADSHEET_ID
        )

    elif file_type == "word":

        spreadsheet_id = (
            WORD_SPREADSHEET_ID
        )

    else:

        raise ValueError(
            "file_type must be 'excel' or 'word'"
        )

    # --------------------------------------------------------
    # READ EMAIL COLUMN
    # --------------------------------------------------------

    result = service.spreadsheets().values().get(

        spreadsheetId=spreadsheet_id,

        # Uses the first sheet.
        # Does not depend on "Sheet1".

        range="B2:B10000",

    ).execute()

    # --------------------------------------------------------
    # GET VALUES
    # --------------------------------------------------------

    values = result.get(
        "values",
        [],
    )

    # --------------------------------------------------------
    # CHECK EMAIL
    # --------------------------------------------------------

    for row in values:

        if not row:
            continue

        existing_email = str(
            row[0]
        ).strip().lower()

        if existing_email == email:

            print(
                f"⚠️ Duplicate email found: "
                f"{email} | "
                f"Type: {file_type}"
            )

            return True

    # --------------------------------------------------------
    # EMAIL NOT FOUND
    # --------------------------------------------------------

    print(
        f"✅ Email is available: "
        f"{email} | "
        f"Type: {file_type}"
    )

    return False


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # TEST EXCEL
    # --------------------------------------------------------

    save_student_result(

        student_name="Ali",

        email="ali@example.com",

        attendance_number="01",

        grade="10A",

        project_id="project_1",

        score=16,

        max_score=20,

        status="PASSED",

        feedback=(
            "The Excel project was "
            "graded successfully."
        ),
    )

    # --------------------------------------------------------
    # TEST WORD
    # --------------------------------------------------------

    save_word_student_result(

        student_name="Ali",

        email="ali@example.com",

        attendance_number="01",

        grade="10A",

        project_id="project_1",

        score=17,

        max_score=20,

        status="PASSED",

        feedback=(
            "The Word project was "
            "graded successfully."
        ),
    )