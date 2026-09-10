import os
import re
import shutil
import uuid

from pathlib import Path

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Query
)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware


from google_services.sheets_service import (
    save_student_result,
    email_exists,
)
from google_services.drive_service import (
    upload_file_to_drive,
    get_student_grade_folder,
    get_master_project_folder,
)


from analyzer.excel_analyzer import extract_full_rules

from analyzer.rule_engine import (
    load_master_rules,
    save_master_rules,
    compare_structure,
)


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="Auto Grader API",
    description="Flexible educational project grading system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# FRONTEND
# =========================================================

FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "frontend"
)


app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)


# =========================================================
# FRONTEND PAGES
# =========================================================

@app.get("/")
def home():
    """
    Main student grading page.
    """

    return FileResponse(
        os.path.join(
            FRONTEND_DIR,
            "index.html"
        )
    )


@app.get("/teacher")
def teacher_page():
    """
    Teacher dashboard.
    """

    return FileResponse(
        os.path.join(
            FRONTEND_DIR,
            "teacher.html"
        )
    )


@app.get("/grade/{grade}")
def grade_page(grade: str):
    """
    Student grading page.

    Examples:

        /grade/10a
        /grade/10b
        /grade/11a
        /grade/11b

    The grade is taken automatically from the URL.
    """

    grade = grade.strip().upper()

    if not grade:
        raise HTTPException(
            status_code=400,
            detail="Grade is required."
        )

    return FileResponse(
        os.path.join(
            FRONTEND_DIR,
            "index.html"
        )
    )


# =========================================================
# UPLOAD FOLDER
# =========================================================

UPLOAD_FOLDER = Path("uploads")

UPLOAD_FOLDER.mkdir(
    exist_ok=True
)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# =========================================================
# GRADE VALIDATION
# =========================================================

def normalize_grade(grade: str) -> str:
    """
    Normalize grade from URL.

    Examples:

        10a -> 10A
        10A -> 10A
        11b -> 11B
    """

    if grade is None:
        raise HTTPException(
            status_code=400,
            detail="Grade is required."
        )

    grade = str(grade).strip().upper()

    if not grade:
        raise HTTPException(
            status_code=400,
            detail="Grade cannot be empty."
        )

    return grade


# =========================================================
# STUDENT EXCEL GRADING
# =========================================================

@app.post("/grade/{grade}/excel")
async def grade_excel(
    grade: str,

    file: UploadFile = File(...),

    project_id: str = Query(
        ...,
        description="Master project ID"
    ),

    student_name: str = Query(
        ...,
        description="Student name"
    ),

    attendance_number: str = Query(
        ...,
        description="Student attendance number"
    ),

    email: str = Query(
    ...,
    description="Student email"
    )
):
    """
    Grade a student's Excel project.

    Grade is NOT entered manually by the student.

    It comes from the URL:

        /grade/10a/excel
        /grade/10b/excel
        /grade/11a/excel
        /grade/11b/excel

    Student provides:

        - Name
        - Attendance number
        - Project ID
        - Excel file
    """

    # -----------------------------------------------------
    # NORMALIZE DATA
    # -----------------------------------------------------

    grade = normalize_grade(grade)

    student_name = str(
        student_name
    ).strip()

    attendance_number = str(
        attendance_number
    ).strip()

    email = str(
        email
    ).strip().lower()

    project_id = str(
        project_id
    ).strip()


    # -----------------------------------------------------
    # VALIDATE STUDENT NAME
    # -----------------------------------------------------

    if not student_name:
        raise HTTPException(
            status_code=400,
            detail="Student name is required."
        )


    # -----------------------------------------------------
    # VALIDATE ATTENDANCE NUMBER
    # -----------------------------------------------------

    if not attendance_number:
        raise HTTPException(
            status_code=400,
            detail="Attendance number is required."
        )


    # -----------------------------------------------------
    # CHECK DUPLICATE EMAIL
    # -----------------------------------------------------

    if email_exists(email):

        raise HTTPException(
            status_code=409,
            detail=(
                "This email has already been used "
                "to submit a project. "
                "Another submission is not allowed."
            )
      )
    # -----------------------------------------------------
    # VALIDATE PROJECT ID
    # -----------------------------------------------------

    if not project_id:
        raise HTTPException(
            status_code=400,
            detail="Project ID is required."
        )


    # -----------------------------------------------------
    # VALIDATE FILE
    # -----------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file was uploaded."
        )


    filename_lower = file.filename.lower()

    if not filename_lower.endswith(
        (
            ".xlsx",
            ".xlsm"
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="Only Excel files (.xlsx, .xlsm) are allowed."
        )


    # -----------------------------------------------------
    # CREATE UNIQUE FILE NAME
    # -----------------------------------------------------

    file_id = uuid.uuid4().hex

    safe_filename = (
        f"{file_id}_{file.filename}"
    )

    file_path = (
        UPLOAD_FOLDER /
        safe_filename
    )


    # -----------------------------------------------------
    # SAVE UPLOADED FILE
    # -----------------------------------------------------

    try:

        with file_path.open("wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not save uploaded file: "
                f"{str(e)}"
            )
        )


    # -----------------------------------------------------
    # LOAD MASTER RULES
    # -----------------------------------------------------

    master_rules = load_master_rules(
        project_id
    )


    if master_rules is None:

        if file_path.exists():

            try:
                file_path.unlink()
            except Exception:
                pass

        raise HTTPException(
            status_code=404,
            detail=(
                f"Master rules for "
                f"{project_id} were not found."
            )
        )


    # -----------------------------------------------------
    # ANALYZE STUDENT EXCEL
    # -----------------------------------------------------

    try:

        student_rules = extract_full_rules(
            str(file_path)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not analyze Excel file: "
                f"{str(e)}"
            )
        )


    # -----------------------------------------------------
    # COMPARE WITH MASTER
    # -----------------------------------------------------

    try:

        result = compare_structure(
            student_rules,
            master_rules
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Grading failed: "
                f"{str(e)}"
            )
        )


    # -----------------------------------------------------
    # UPLOAD TO GOOGLE DRIVE
    # -----------------------------------------------------

    drive_file = None

    try:

        grade_folder = get_student_grade_folder(
            project_id=project_id,
            grade=grade
        )

        drive_file = upload_file_to_drive(
            file_path=str(file_path),
            file_name=file.filename,
            folder_id=grade_folder["id"]
        )

        print(
            "✅ Student file saved to Google Drive: "
            f"{file.filename}"
        )

    except Exception as e:

        print(
            "⚠️ Google Drive upload failed: "
            f"{e}"
        )


    # -----------------------------------------------------
    # BUILD FEEDBACK
    # -----------------------------------------------------

    try:

        ai_feedback = result.get(
            "ai_feedback"
        )


        if (
            isinstance(
                ai_feedback,
                str
            )
            and ai_feedback.strip()
        ):

            feedback = ai_feedback


        else:

            feedback_items = result.get(
                "student_feedback",
                []
            )

            messages = []


            for item in feedback_items:

                if isinstance(
                    item,
                    dict
                ):

                    message = item.get(
                        "message",
                        ""
                    )

                    if message:

                        messages.append(
                            message
                        )


            feedback = "\n".join(
                messages
            )


        if not isinstance(
            feedback,
            str
        ):

            feedback = str(
                feedback
            )


    except Exception as e:

        print(
            "⚠️ Feedback processing failed: "
            f"{e}"
        )

        feedback = ""


    # -----------------------------------------------------
    # SAVE RESULT TO GOOGLE SHEETS
    # -----------------------------------------------------

    try:

        save_student_result(

            student_name=student_name,

            email=email,

            attendance_number=attendance_number,

            grade=grade,

            project_id=project_id,

            score=result["score"],

            max_score=result["max_score"],

            status=result["status"],

            feedback=feedback
        )


        print(
            "✅ Student grading result "
            "saved to Google Sheets."
        )


    except Exception as e:

        print(
            "⚠️ Google Sheets save failed: "
            f"{e}"
        )


    # -----------------------------------------------------
# DELETE TEMPORARY STUDENT FILE
# -----------------------------------------------------

    if file_path.exists():

        try:

            file_path.unlink()

            print(
                f"🗑️ Temporary student file deleted: "
                f"{file_path.name}"
            )

        except Exception as e:

            print(
                "⚠️ Could not delete temporary "
                f"student file: {e}"
            )


    # -----------------------------------------------------
    # RETURN RESULT TO FRONTEND
    # -----------------------------------------------------

    return {

        "success": True,

        "student_name": student_name,

        "email": email,

        "attendance_number": attendance_number,

        "grade": grade,

        "filename": file.filename,

        "project_id": project_id,

        "score": result["score"],

        "max_score": result["max_score"],

        "status": result["status"],

        "passed": result["passed"],

        "checks": {

            "passed": result[
                "checks_passed"
            ],

            "total": result[
                "total_checks"
            ]

        },

        "score_details": result[
            "score_details"
        ],

        "errors": result[
            "errors"
        ],

        "student_feedback": result[
            "student_feedback"
        ],

        "ai_feedback": result.get(
            "ai_feedback"
        ),

        "summary": result[
            "summary"
        ],

        "google_drive": {

            "uploaded": (
                drive_file is not None
            ),

            "file_id": (
                drive_file.get("id")
                if drive_file
                else None
            ),

            "file_name": (
                drive_file.get("name")
                if drive_file
                else None
            ),

            "web_view_link": (
                drive_file.get(
                    "webViewLink"
                )
                if drive_file
                else None
            )

        }

    }


# =========================================================
# TEACHER - CREATE MASTER PROJECT
# =========================================================

@app.post("/teacher/create-project")
async def create_project(
    project_id: str,
    file: UploadFile = File(...)
):
    """
    Create/update a Master Project from an Excel file.

    This remains flexible because the rules are extracted
    from the uploaded Master Excel file.
    """

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was uploaded."
        )


    if not file.filename.lower().endswith(
        (
            ".xlsx",
            ".xlsm"
        )
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only Excel files "
                "(.xlsx, .xlsm) are allowed."
            )
        )


    project_id = str(
        project_id
    ).strip()


    if not project_id:

        raise HTTPException(
            status_code=400,
            detail="Project ID is required."
        )


    file_id = uuid.uuid4().hex

    safe_filename = (
        f"master_{file_id}_{file.filename}"
    )

    file_path = (
        UPLOAD_FOLDER /
        safe_filename
    )


    try:

        with file_path.open("wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not save master file: "
                f"{str(e)}"
            )
        )


    # -----------------------------------------------------
    # EXTRACT RULES
    # -----------------------------------------------------

    try:

        master_rules = extract_full_rules(
            str(file_path)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not analyze master Excel: "
                f"{str(e)}"
            )
        )


    # -----------------------------------------------------
    # SAVE RULES
    # -----------------------------------------------------

    try:

        save_master_rules(
            master_rules,
            project_id
            
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not save master rules: "
                f"{str(e)}"
            )
        )


    # -----------------------------------------------------
    # OPTIONAL DRIVE UPLOAD
    # -----------------------------------------------------

    drive_file = None

    try:

        master_folder = get_master_project_folder(
            project_id
        )

        drive_file = upload_file_to_drive(
            file_path=str(file_path),
            file_name="master.xlsx",
            folder_id=master_folder["id"]
        )

        print(
            "✅ Master project uploaded to Drive."
        )

    except Exception as e:

        print(
            "⚠️ Master Drive upload failed: "
            f"{e}"
        )

    # -----------------------------------------------------
# DELETE TEMPORARY MASTER FILE
# -----------------------------------------------------

    if file_path.exists():

        try:

            file_path.unlink()

            print(
                f"🗑️ Temporary master file deleted: "
                f"{file_path.name}"
            )

        except Exception as e:

            print(
                "⚠️ Could not delete temporary "
                f"master file: {e}"
            )

    return {

        "success": True,

        "message": (
            "Master project created successfully."
        ),

        "project_id": project_id,

        "filename": file.filename,

        "google_drive": {

            "uploaded": (
                drive_file is not None
            ),

            "file_id": (
                drive_file.get("id")
                if drive_file
                else None
            ),

            "web_view_link": (
                drive_file.get(
                    "webViewLink"
                )
                if drive_file
                else None
            )

        }

    }