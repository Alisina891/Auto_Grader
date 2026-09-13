import os
import shutil
import uuid

from pathlib import Path

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Query,
)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware


# =========================================================
# GOOGLE SERVICES
# =========================================================

from google_services.sheets_service import (
    save_student_result,
    save_word_student_result,
    email_exists,
)

from google_services.drive_service import (
    upload_file_to_drive,
    get_student_grade_folder,
)


# =========================================================
# EXCEL
# =========================================================

from analyzer.excel_analyzer import (
    extract_full_rules as extract_excel_rules,
)

from analyzer.rule_engine import (
    load_master_rules as load_excel_master_rules,
    save_master_rules as save_excel_master_rules,
    compare_structure,
)


# =========================================================
# WORD
# =========================================================

from analyzer.word.word_report_generator import (
    create_word_master_project,
    grade_word_files,
)


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="Auto Grader API",
    description="Flexible educational project grading system",
    version="1.1.0",
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
    os.path.dirname(
        os.path.dirname(__file__)
    ),
    "frontend",
)


app.mount(
    "/static",
    StaticFiles(
        directory=FRONTEND_DIR
    ),
    name="static",
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
            "index.html",
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
            "teacher.html",
        )
    )


@app.get("/grade/{grade}")
def grade_page(
    grade: str,
):
    """
    Student grading page.

    Grade is taken automatically from the URL.
    """

    grade = normalize_grade(
        grade
    )

    return FileResponse(
        os.path.join(
            FRONTEND_DIR,
            "index.html",
        )
    )


# =========================================================
# UPLOAD FOLDER
# =========================================================

UPLOAD_FOLDER = Path(
    "uploads"
)

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

def normalize_grade(
    grade: str,
) -> str:
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
            detail="Grade is required.",
        )

    grade = str(
        grade
    ).strip().upper()

    if not grade:

        raise HTTPException(
            status_code=400,
            detail="Grade cannot be empty.",
        )

    return grade


# =========================================================
# PROJECT ID VALIDATION
# =========================================================

def normalize_project_id(
    project_id: str,
) -> str:
    """
    Normalize project ID.
    """

    if project_id is None:

        raise HTTPException(
            status_code=400,
            detail="Project ID is required.",
        )

    project_id = str(
        project_id
    ).strip()

    if not project_id:

        raise HTTPException(
            status_code=400,
            detail="Project ID cannot be empty.",
        )

    return project_id


# =========================================================
# STUDENT DATA VALIDATION
# =========================================================

def normalize_student_data(
    student_name: str,
    attendance_number: str,
    email: str,
):
    """
    Normalize student information.
    """

    student_name = str(
        student_name
    ).strip()

    attendance_number = str(
        attendance_number
    ).strip()

    email = str(
        email
    ).strip().lower()

    if not student_name:

        raise HTTPException(
            status_code=400,
            detail="Student name is required.",
        )

    if not attendance_number:

        raise HTTPException(
            status_code=400,
            detail="Attendance number is required.",
        )

    if not email:

        raise HTTPException(
            status_code=400,
            detail="Student email is required.",
        )

    return (
        student_name,
        attendance_number,
        email,
    )


# =========================================================
# SAVE UPLOADED FILE
# =========================================================

def save_uploaded_file(
    file: UploadFile,
    prefix: str,
) -> Path:
    """
    Save uploaded file to temporary uploads folder.
    """

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was uploaded.",
        )

    file_id = uuid.uuid4().hex

    safe_filename = (
        f"{prefix}_{file_id}_{file.filename}"
    )

    file_path = (
        UPLOAD_FOLDER /
        safe_filename
    )

    try:

        with file_path.open(
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not save uploaded file: "
                f"{error}"
            ),
        )

    return file_path


# =========================================================
# DELETE TEMP FILE
# =========================================================

def delete_temp_file(
    file_path: Path,
):
    """
    Delete temporary uploaded file.
    """

    if not file_path.exists():
        return

    try:

        file_path.unlink()

        print(
            f"🗑️ Temporary file deleted: "
            f"{file_path.name}"
        )

    except Exception as error:

        print(
            "⚠️ Could not delete temporary file: "
            f"{error}"
        )


# =========================================================
# STUDENT EXCEL GRADING
# =========================================================

@app.post(
    "/grade/{grade}/excel"
)
async def grade_excel(
    grade: str,

    file: UploadFile = File(...),

    project_id: str = Query(
        ...,
        description="Master project ID",
    ),

    student_name: str = Query(
        ...,
        description="Student name",
    ),

    attendance_number: str = Query(
        ...,
        description="Student attendance number",
    ),

    email: str = Query(
        ...,
        description="Student email",
    ),
):
    """
    Grade a student's Excel project.
    """

    # -----------------------------------------------------
    # NORMALIZE
    # -----------------------------------------------------

    grade = normalize_grade(
        grade
    )

    project_id = normalize_project_id(
        project_id
    )

    (
        student_name,
        attendance_number,
        email,
    ) = normalize_student_data(
        student_name,
        attendance_number,
        email,
    )


    # -----------------------------------------------------
    # CHECK DUPLICATE EMAIL - EXCEL ONLY
    # -----------------------------------------------------

    if email_exists(
        email,
        file_type="excel",
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "This email has already been used "
                "to submit an Excel project."
            ),
        )


    # -----------------------------------------------------
    # VALIDATE FILE
    # -----------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was uploaded.",
        )

    filename_lower = (
        file.filename.lower()
    )

    if not filename_lower.endswith(
        (
            ".xlsx",
            ".xlsm",
        )
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only Excel files "
                "(.xlsx, .xlsm) are allowed."
            ),
        )


    # -----------------------------------------------------
    # SAVE FILE
    # -----------------------------------------------------

    file_path = save_uploaded_file(
        file,
        "student_excel",
    )


    try:

        # -------------------------------------------------
        # LOAD EXCEL MASTER RULES
        # -------------------------------------------------

        master_rules = (
            load_excel_master_rules(
                project_id
            )
        )

        if master_rules is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Excel master rules for "
                    f"Project {project_id} "
                    f"were not found."
                ),
            )


        # -------------------------------------------------
        # ANALYZE STUDENT EXCEL
        # -------------------------------------------------

        try:

            student_rules = (
                extract_excel_rules(
                    str(file_path)
                )
            )

        except Exception as error:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Could not analyze Excel file: "
                    f"{error}"
                ),
            )


        # -------------------------------------------------
        # COMPARE
        # -------------------------------------------------

        try:

            result = compare_structure(
                student_rules,
                master_rules,
            )

        except Exception as error:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Excel grading failed: "
                    f"{error}"
                ),
            )


        # -------------------------------------------------
        # GOOGLE DRIVE - STUDENT EXCEL ONLY
        # -------------------------------------------------

        drive_file = None

        try:

            grade_folder = (
                get_student_grade_folder(
                    project_id=project_id,
                    grade=grade,
                    file_type="excel",
                )
            )

            drive_file = (
                upload_file_to_drive(
                    file_path=str(
                        file_path
                    ),
                    file_name=file.filename,
                    folder_id=grade_folder["id"],
                )
            )

            print(
                "✅ Student Excel file "
                "saved to Google Drive."
            )

        except Exception as error:

            print(
                "⚠️ Google Drive upload failed: "
                f"{error}"
            )


        # -------------------------------------------------
        # FEEDBACK
        # -------------------------------------------------

        feedback = ""

        try:

            ai_feedback = result.get(
                "ai_feedback"
            )

            if (
                isinstance(
                    ai_feedback,
                    str,
                )
                and ai_feedback.strip()
            ):

                feedback = ai_feedback

            else:

                feedback_items = result.get(
                    "student_feedback",
                    [],
                )

                messages = []

                for item in feedback_items:

                    if isinstance(
                        item,
                        dict,
                    ):

                        message = item.get(
                            "message",
                            "",
                        )

                        if message:

                            messages.append(
                                message
                            )

                feedback = "\n".join(
                    messages
                )

        except Exception as error:

            print(
                "⚠️ Excel feedback processing failed: "
                f"{error}"
            )

            feedback = ""


        # -------------------------------------------------
        # GOOGLE SHEETS - EXCEL
        # -------------------------------------------------

        try:

            save_student_result(

                student_name=student_name,

                email=email,

                attendance_number=(
                    attendance_number
                ),

                grade=grade,

                project_id=project_id,

                score=result["score"],

                max_score=result["max_score"],

                status=result["status"],

                feedback=feedback,
            )

            print(
                "✅ Excel grading result "
                "saved to Google Sheets."
            )

        except Exception as error:

            print(
                "⚠️ Google Sheets save failed: "
                f"{error}"
            )


        # -------------------------------------------------
        # RETURN EXCEL RESULT
        # -------------------------------------------------

        return {

            "success": True,

            "file_type": "excel",

            "student_name": student_name,

            "email": email,

            "attendance_number": (
                attendance_number
            ),

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
                ],
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
                ),
            },
        }

    finally:

        # -------------------------------------------------
        # DELETE TEMP FILE
        # -------------------------------------------------

        delete_temp_file(
            file_path
        )


# =========================================================
# STUDENT WORD GRADING
# =========================================================

@app.post(
    "/grade/{grade}/word"
)
async def grade_word(
    grade: str,

    file: UploadFile = File(...),

    project_id: str = Query(
        ...,
        description="Master Word project ID",
    ),

    student_name: str = Query(
        ...,
        description="Student name",
    ),

    attendance_number: str = Query(
        ...,
        description="Student attendance number",
    ),

    email: str = Query(
        ...,
        description="Student email",
    ),
):
    """
    Grade a student's Word project.

    Master Word rules are stored locally.
    Student Word files are saved to Google Drive.
    Word results are saved to the Word Google Sheet.
    """

    # -----------------------------------------------------
    # NORMALIZE
    # -----------------------------------------------------

    grade = normalize_grade(
        grade
    )

    project_id = normalize_project_id(
        project_id
    )

    (
        student_name,
        attendance_number,
        email,
    ) = normalize_student_data(
        student_name,
        attendance_number,
        email,
    )


    # -----------------------------------------------------
    # CHECK DUPLICATE EMAIL - WORD ONLY
    # -----------------------------------------------------

    if email_exists(
        email,
        file_type="word",
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "This email has already been used "
                "to submit a Word project."
            ),
        )


    # -----------------------------------------------------
    # VALIDATE WORD FILE
    # -----------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was uploaded.",
        )

    filename_lower = (
        file.filename.lower()
    )

    if not filename_lower.endswith(
        ".docx"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only Word files (.docx) "
                "are allowed."
            ),
        )


    # -----------------------------------------------------
    # SAVE FILE
    # -----------------------------------------------------

    file_path = save_uploaded_file(
        file,
        "student_word",
    )


    try:

        # -------------------------------------------------
        # GRADE WORD PROJECT
        # -------------------------------------------------

        try:

            report = grade_word_files(

                student_file=str(
                    file_path
                ),

                student_name=student_name,

                attendance_number=(
                    attendance_number
                ),

                grade=grade,

                project_id=project_id,

                include_ai=True,
            )

        except FileNotFoundError as error:

            raise HTTPException(
                status_code=404,
                detail=str(error),
            )

        except Exception as error:

            print(
                "❌ Word grading error: "
                f"{error}"
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Word grading failed: "
                    f"{error}"
                ),
            )


        # -------------------------------------------------
        # CHECK COMPARISON
        # -------------------------------------------------

        comparison = report.get(
            "comparison",
            {},
        )

        if not comparison.get(
            "success",
            False,
        ):

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Word master project "
                    f"{project_id} was not found."
                ),
            )


        # -------------------------------------------------
        # SCORE
        # -------------------------------------------------

        score_data = report.get(
            "score",
            {},
        )

        score = score_data.get(
            "score",
            0,
        )

        max_score = score_data.get(
            "max_score",
            20,
        )

        status = score_data.get(
            "status",
            "FAILED",
        )

        passed = score_data.get(
            "passed",
            False,
        )


        # -------------------------------------------------
        # ERRORS
        # -------------------------------------------------

        scoring = report.get(
            "scoring",
            {},
        )

        errors = report.get(
            "errors",
            {},
        )

        category_deductions = report.get(
            "category_deductions",
            {},
        )


        # -------------------------------------------------
        # FEEDBACK
        # -------------------------------------------------

        deterministic_feedback = (
            report.get(
                "feedback",
                [],
            )
        )

        ai_data = report.get(
            "ai",
            {},
        )

        ai_feedback = ai_data.get(
            "feedback"
        )


        # -------------------------------------------------
        # BUILD SHEETS FEEDBACK
        # -------------------------------------------------

        feedback_text = ""

        if (
            isinstance(
                ai_feedback,
                str,
            )
            and ai_feedback.strip()
        ):

            feedback_text = ai_feedback

        elif isinstance(
            deterministic_feedback,
            list,
        ):

            messages = []

            for item in (
                deterministic_feedback
            ):

                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                message = item.get(
                    "message",
                    "",
                )

                if message:

                    messages.append(
                        message
                    )

            feedback_text = "\n".join(
                messages
            )

        elif isinstance(
            deterministic_feedback,
            str,
        ):

            feedback_text = (
                deterministic_feedback
            )


        # -------------------------------------------------
        # GOOGLE DRIVE - STUDENT WORD ONLY
        # -------------------------------------------------

        drive_file = None

        try:

            grade_folder = (
                get_student_grade_folder(
                    project_id=project_id,
                    grade=grade,
                    file_type="word",
                )
            )

            drive_file = (
                upload_file_to_drive(
                    file_path=str(
                        file_path
                    ),
                    file_name=file.filename,
                    folder_id=grade_folder["id"],
                )
            )

            print(
                "✅ Student Word file "
                "saved to Google Drive."
            )

        except Exception as error:

            print(
                "⚠️ Word Google Drive upload failed: "
                f"{error}"
            )


        # -------------------------------------------------
        # GOOGLE SHEETS - WORD
        # -------------------------------------------------

        try:

            save_word_student_result(

                student_name=student_name,

                email=email,

                attendance_number=(
                    attendance_number
                ),

                grade=grade,

                project_id=project_id,

                score=score,

                max_score=max_score,

                status=status,

                feedback=feedback_text,
            )

            print(
                "✅ Word grading result "
                "saved to Word Google Sheets."
            )

        except Exception as error:

            print(
                "⚠️ Word Google Sheets save failed: "
                f"{error}"
            )


        # -------------------------------------------------
        # RETURN WORD RESULT
        # -------------------------------------------------

        return {

            "success": True,

            "file_type": "word",

            "student_name": student_name,

            "email": email,

            "attendance_number": (
                attendance_number
            ),

            "grade": grade,

            "filename": file.filename,

            "project_id": project_id,

            "score": score,

            "max_score": max_score,

            "status": status,

            "passed": passed,

            "passing_score": score_data.get(
                "passing_score",
                12,
            ),

            "errors": errors,

            "category_deductions": (
                category_deductions
            ),

            "score_details": scoring,

            "student_feedback": (
                deterministic_feedback
            ),

            "ai_feedback": ai_feedback,

            "summary": (
                comparison.get(
                    "summary",
                    {},
                )
            ),

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
                ),
            },
        }

    finally:

        # -------------------------------------------------
        # DELETE TEMP FILE
        # -------------------------------------------------

        delete_temp_file(
            file_path
        )


# =========================================================
# TEACHER - CREATE EXCEL MASTER PROJECT
# =========================================================

@app.post(
    "/teacher/create-project"
)
async def create_project(
    project_id: str,
    file: UploadFile = File(...),
):
    """
    Create/update an Excel Master Project.

    Master rules are stored locally.
    Master files are NOT uploaded to Google Drive.
    """

    # -----------------------------------------------------
    # VALIDATE
    # -----------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was uploaded.",
        )

    if not file.filename.lower().endswith(
        (
            ".xlsx",
            ".xlsm",
        )
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only Excel files "
                "(.xlsx, .xlsm) are allowed."
            ),
        )

    project_id = normalize_project_id(
        project_id
    )


    # -----------------------------------------------------
    # SAVE MASTER FILE TEMPORARILY
    # -----------------------------------------------------

    file_path = save_uploaded_file(
        file,
        "master_excel",
    )


    try:

        # -------------------------------------------------
        # EXTRACT RULES
        # -------------------------------------------------

        try:

            master_rules = (
                extract_excel_rules(
                    str(file_path)
                )
            )

        except Exception as error:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Could not analyze master Excel: "
                    f"{error}"
                ),
            )


        # -------------------------------------------------
        # SAVE MASTER RULES LOCALLY
        # -------------------------------------------------

        try:

            rules_path = (
                save_excel_master_rules(
                    master_rules,
                    project_id,
                )
            )

        except Exception as error:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Could not save Excel master rules: "
                    f"{error}"
                ),
            )


        # -------------------------------------------------
        # RETURN
        # -------------------------------------------------

        return {

            "success": True,

            "message": (
                "Excel Master project "
                "created successfully."
            ),

            "project_type": "excel",

            "project_id": project_id,

            "filename": file.filename,

            "master_rules_path": rules_path,

            "google_drive": {

                "uploaded": False,

                "message": (
                    "Master Excel is stored locally "
                    "and is not uploaded to Google Drive."
                ),
            },
        }

    finally:

        # -------------------------------------------------
        # DELETE TEMP MASTER
        # -------------------------------------------------

        delete_temp_file(
            file_path
        )


# =========================================================
# TEACHER - CREATE WORD MASTER PROJECT
# =========================================================

@app.post(
    "/teacher/create-word-project"
)
async def create_word_project(
    project_id: str,
    file: UploadFile = File(...),
):
    """
    Create/update a Word Master Project.

    Master rules are stored locally.

    Google Drive is NOT used for Master Word files.
    """

    # -----------------------------------------------------
    # VALIDATE PROJECT
    # -----------------------------------------------------

    project_id = normalize_project_id(
        project_id
    )


    # -----------------------------------------------------
    # VALIDATE FILE
    # -----------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was uploaded.",
        )

    if not file.filename.lower().endswith(
        ".docx"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only Word files (.docx) "
                "are allowed."
            ),
        )


    # -----------------------------------------------------
    # SAVE TEMP MASTER
    # -----------------------------------------------------

    file_path = save_uploaded_file(
        file,
        "master_word",
    )


    try:

        # -------------------------------------------------
        # CREATE / REPLACE MASTER RULES
        # -------------------------------------------------

        try:

            master_result = (
                create_word_master_project(

                    master_file=str(
                        file_path
                    ),

                    project_id=project_id,
                )
            )

        except Exception as error:

            print(
                "❌ Word Master creation failed: "
                f"{error}"
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Could not create Word "
                    "master project: "
                    f"{error}"
                ),
            )


        # -------------------------------------------------
        # RETURN
        # -------------------------------------------------

        return {

            "success": True,

            "message": (
                "Word Master project "
                "created successfully."
            ),

            "project_type": "word",

            "project_id": project_id,

            "filename": file.filename,

            "master_rules_path": (
                master_result.get(
                    "master_rules_path"
                )
            ),

            "google_drive": {

                "uploaded": False,

                "message": (
                    "Master Word is stored locally "
                    "and is not uploaded to Google Drive."
                ),
            },
        }

    finally:

        # -------------------------------------------------
        # DELETE TEMP MASTER
        # -------------------------------------------------

        delete_temp_file(
            file_path
        )