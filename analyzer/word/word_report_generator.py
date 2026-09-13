# ============================================================
# WORD REPORT GENERATOR
# ============================================================

import json
import os
from typing import Any, Dict, List, Optional


# ============================================================
# IMPORTS
# ============================================================

from analyzer.word.word_rule_engine import (
    compare_word_files,
    compare_student_with_master,
    create_master_rules_from_word,
    load_master_rules,
)

from analyzer.word.word_scoring_engine import (
    get_score_details,
    MAX_SCORE,
    PASSING_SCORE,
)

from analyzer.word.word_feedback_engine import (
    generate_feedback,
)

from analyzer.word.word_ai_feedback import (
    generate_ai_enhanced_feedback,
)


# ============================================================
# REPORT VERSION
# ============================================================

REPORT_VERSION = "1.1"


# ============================================================
# HELPERS
# ============================================================

def safe_string(value: Any) -> str:
    """
    Safely convert a value to a string.
    """

    if value is None:
        return ""

    return str(value).strip()


def safe_int(
    value: Any,
    default: int = 0
) -> int:
    """
    Safely convert a value to an integer.
    """

    try:
        return int(round(float(value)))

    except (TypeError, ValueError):
        return default


# ============================================================
# STUDENT INFORMATION
# ============================================================

def build_student_info(
    student_name: Optional[str] = None,
    attendance_number: Optional[str] = None,
    grade: Optional[str] = None,
    project_id: Optional[Any] = None,
) -> Dict[str, Any]:

    return {
        "student_name": safe_string(
            student_name
        ),

        "attendance_number": safe_string(
            attendance_number
        ),

        "grade": safe_string(
            grade
        ),

        "project_id": safe_string(
            project_id
        ),
    }


# ============================================================
# FILE INFORMATION
# ============================================================

def build_file_info(
    master_file: Optional[str] = None,
    student_file: Optional[str] = None,
) -> Dict[str, Any]:

    return {
        "master_file": (
            os.path.basename(master_file)
            if master_file
            else ""
        ),

        "student_file": (
            os.path.basename(student_file)
            if student_file
            else ""
        ),
    }


# ============================================================
# SCORE SUMMARY
# ============================================================

def build_score_summary(
    score_details: Dict[str, Any]
) -> Dict[str, Any]:

    final_score = safe_int(
        score_details.get(
            "final_score",
            0
        )
    )

    total_deduction = safe_int(
        score_details.get(
            "total_deduction",
            0
        )
    )

    status = safe_string(
        score_details.get(
            "status",
            "FAILED"
        )
    )

    passed = bool(
        score_details.get(
            "passed",
            False
        )
    )

    return {
        "score": final_score,

        "max_score": MAX_SCORE,

        "score_display": (
            f"{final_score}/{MAX_SCORE}"
        ),

        "total_deduction": total_deduction,

        "points_lost": total_deduction,

        "status": status,

        "passed": passed,

        "passing_score": PASSING_SCORE,
    }


# ============================================================
# ERROR SUMMARY
# ============================================================

def build_error_summary(
    errors: List[Dict[str, Any]],
    score_details: Dict[str, Any]
) -> Dict[str, Any]:

    if not isinstance(errors, list):
        errors = []

    applied_errors = score_details.get(
        "applied_errors",
        []
    )

    ignored_errors = score_details.get(
        "ignored_errors",
        []
    )

    if not isinstance(
        applied_errors,
        list
    ):
        applied_errors = []

    if not isinstance(
        ignored_errors,
        list
    ):
        ignored_errors = []

    return {
        "error_count": len(errors),

        "applied_error_count": len(
            applied_errors
        ),

        "ignored_error_count": len(
            ignored_errors
        ),
    }


# ============================================================
# CATEGORY SUMMARY
# ============================================================

def build_category_summary(
    score_details: Dict[str, Any]
) -> Dict[str, int]:

    category_deductions = score_details.get(
        "category_deductions",
        {}
    )

    if not isinstance(
        category_deductions,
        dict
    ):
        return {}

    result: Dict[str, int] = {}

    for category, deduction in (
        category_deductions.items()
    ):

        result[
            safe_string(category)
        ] = safe_int(deduction)

    return result


# ============================================================
# DETERMINISTIC FEEDBACK
# ============================================================

def build_deterministic_feedback(
    errors: List[Dict[str, Any]],
    score_details: Dict[str, Any]
) -> List[Dict[str, Any]]:

    try:

        feedback = generate_feedback(
            errors,
            score_details
        )

    except Exception as error:

        print(
            f"⚠️ Word deterministic feedback failed: "
            f"{error}"
        )

        return []

    if not isinstance(
        feedback,
        list
    ):
        return []

    return feedback


# ============================================================
# AI FEEDBACK
# ============================================================

def build_ai_feedback(
    errors: List[Dict[str, Any]],
    score_details: Dict[str, Any],
    deterministic_feedback: List[Dict[str, Any]],
    model: Optional[str] = None,
) -> Dict[str, Any]:

    kwargs = {
        "errors": errors,

        "score_details": score_details,

        "deterministic_feedback": (
            deterministic_feedback
        ),
    }

    if model:
        kwargs["model"] = model

    try:

        result = generate_ai_enhanced_feedback(
            **kwargs
        )

    except Exception as error:

        print(
            f"⚠️ Word AI report generation failed: "
            f"{error}"
        )

        return {
            "ai_available": False,

            "ai_feedback": None,

            "deterministic_feedback": (
                deterministic_feedback
            ),

            "error": str(error),
        }

    if not isinstance(
        result,
        dict
    ):

        return {
            "ai_available": False,

            "ai_feedback": None,

            "deterministic_feedback": (
                deterministic_feedback
            ),
        }

    return {
        "ai_available": bool(
            result.get(
                "ai_available",
                False
            )
        ),

        "ai_feedback": result.get(
            "ai_feedback"
        ),

        "deterministic_feedback": (
            result.get(
                "deterministic_feedback",
                deterministic_feedback
            )
        ),
    }


# ============================================================
# COMPLETE WORD REPORT
# ============================================================

def generate_word_report(
    errors: Optional[
        List[Dict[str, Any]]
    ] = None,

    student_name: Optional[str] = None,

    attendance_number: Optional[str] = None,

    grade: Optional[str] = None,

    project_id: Optional[Any] = None,

    master_file: Optional[str] = None,

    student_file: Optional[str] = None,

    include_ai: bool = True,

    ai_model: Optional[str] = None,
) -> Dict[str, Any]:

    # --------------------------------------------------------
    # Normalize errors
    # --------------------------------------------------------

    if errors is None:
        errors = []

    if not isinstance(
        errors,
        list
    ):
        errors = []


    # --------------------------------------------------------
    # Calculate score
    # --------------------------------------------------------

    score_details = get_score_details(
        errors
    )


    # --------------------------------------------------------
    # Build summaries
    # --------------------------------------------------------

    score_summary = build_score_summary(
        score_details
    )

    error_summary = build_error_summary(
        errors,
        score_details
    )

    category_deductions = (
        build_category_summary(
            score_details
        )
    )


    # --------------------------------------------------------
    # Generate deterministic feedback
    # --------------------------------------------------------

    deterministic_feedback = (
        build_deterministic_feedback(
            errors,
            score_details
        )
    )


    # --------------------------------------------------------
    # Generate AI feedback
    # --------------------------------------------------------

    ai_result = {
        "ai_available": False,

        "ai_feedback": None,

        "deterministic_feedback": (
            deterministic_feedback
        ),
    }

    if include_ai:

        ai_result = build_ai_feedback(

            errors=errors,

            score_details=score_details,

            deterministic_feedback=(
                deterministic_feedback
            ),

            model=ai_model,
        )


    # --------------------------------------------------------
    # Final report
    # --------------------------------------------------------

    report = {

        "success": True,

        "report_type": (
            "word_grading_report"
        ),

        "report_version": (
            REPORT_VERSION
        ),


        # ----------------------------------------------------
        # Student
        # ----------------------------------------------------

        "student": build_student_info(

            student_name=student_name,

            attendance_number=(
                attendance_number
            ),

            grade=grade,

            project_id=project_id,
        ),


        # ----------------------------------------------------
        # Files
        # ----------------------------------------------------

        "files": build_file_info(

            master_file=master_file,

            student_file=student_file,
        ),


        # ----------------------------------------------------
        # Score
        # ----------------------------------------------------

        "score": score_summary,


        # ----------------------------------------------------
        # Errors
        # ----------------------------------------------------

        "errors": error_summary,


        # ----------------------------------------------------
        # Category deductions
        # ----------------------------------------------------

        "category_deductions": (
            category_deductions
        ),


        # ----------------------------------------------------
        # Deterministic feedback
        # ----------------------------------------------------

        "feedback": (
            deterministic_feedback
        ),


        # ----------------------------------------------------
        # AI feedback
        # ----------------------------------------------------

        "ai": {

            "available": ai_result.get(
                "ai_available",
                False
            ),

            "feedback": ai_result.get(
                "ai_feedback"
            ),
        },


        # ----------------------------------------------------
        # Full scoring details
        # ----------------------------------------------------

        "scoring": score_details,
    }

    return report


# ============================================================
# MASTER PROJECT CREATION
# ============================================================

def create_word_master_project(
    master_file: str,
    project_id: Any,
) -> Dict[str, Any]:
    """
    Create or replace a Word Master Project.

    Flow:

        Master DOCX
            ↓
        word_analyzer
            ↓
        word rules
            ↓
        master_word.json

    Existing rules for the same project_id are replaced.
    """

    if not master_file:

        raise ValueError(
            "master_file is required."
        )

    if not os.path.exists(
        master_file
    ):

        raise FileNotFoundError(
            f"Master Word file not found: "
            f"{master_file}"
        )

    extension = os.path.splitext(
        master_file
    )[1].lower()

    if extension != ".docx":

        raise ValueError(
            "Word Master file must be a .docx file."
        )

    if project_id is None:

        raise ValueError(
            "project_id is required."
        )

    try:

        result = create_master_rules_from_word(
            master_filepath=master_file,
            project_id=project_id,
        )

    except Exception as error:

        print(
            f"❌ Word Master creation failed: "
            f"{error}"
        )

        raise

    return {
        "success": True,

        "project_id": safe_string(
            project_id
        ),

        "master_file": os.path.basename(
            master_file
        ),

        "master_rules_path": result.get(
            "master_rules_path"
        ),
    }


# ============================================================
# COMPLETE WORD GRADING PIPELINE
# ============================================================

def grade_word_files(
    master_file: Optional[str] = None,

    student_file: Optional[str] = None,

    student_name: Optional[str] = None,

    attendance_number: Optional[str] = None,

    grade: Optional[str] = None,

    project_id: Optional[Any] = None,

    include_ai: bool = True,

    ai_model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Complete Word grading pipeline.

    Preferred production flow:

        project_id
             ↓
        load master_word.json
             ↓
        extract student rules
             ↓
        compare
             ↓
        scoring
             ↓
        feedback
             ↓
        AI wording

    Backward-compatible flow:

        master_file + student_file
             ↓
        compare_word_files()
    """

    # --------------------------------------------------------
    # Check student file
    # --------------------------------------------------------

    if not student_file:

        raise ValueError(
            "student_file is required."
        )

    if not os.path.exists(
        student_file
    ):

        raise FileNotFoundError(
            f"Student Word file not found: "
            f"{student_file}"
        )

    student_extension = (
        os.path.splitext(
            student_file
        )[1].lower()
    )

    if student_extension != ".docx":

        raise ValueError(
            "Student Word file must be a .docx file."
        )


    # ========================================================
    # PRODUCTION MODE
    # ========================================================
    #
    # If project_id is provided, use the stored
    # master_word.json.
    #
    # The Master DOCX does NOT need to be read again.
    # ========================================================

    if project_id is not None:

        print(
            f"📘 Loading Word Master rules "
            f"for Project {project_id}..."
        )

        comparison_result = (
            compare_student_with_master(
                student_filepath=student_file,

                project_id=project_id,
            )
        )

        # ----------------------------------------------------
        # Master file information
        # ----------------------------------------------------

        stored_master_file = (
            master_file
        )

        if not stored_master_file:

            stored_master_file = (
                f"project_{project_id}"
            )


        # ----------------------------------------------------
        # Get errors
        # ----------------------------------------------------

        errors = comparison_result.get(
            "errors",
            []
        )

        if not isinstance(
            errors,
            list
        ):
            errors = []


        # ----------------------------------------------------
        # Generate report
        # ----------------------------------------------------

        report = generate_word_report(

            errors=errors,

            student_name=student_name,

            attendance_number=(
                attendance_number
            ),

            grade=grade,

            project_id=project_id,

            master_file=(
                stored_master_file
            ),

            student_file=student_file,

            include_ai=include_ai,

            ai_model=ai_model,
        )


        # ----------------------------------------------------
        # Add comparison information
        # ----------------------------------------------------

        report["comparison"] = {

            "success": bool(
                comparison_result.get(
                    "success",
                    False
                )
            ),

            "mode": "stored_master_rules",

            "project_id": safe_string(
                project_id
            ),

            "master_rules_loaded": (
                comparison_result.get(
                    "success",
                    False
                )
            ),

            "student_file": (
                comparison_result.get(
                    "student_file",
                    student_file
                )
            ),

            "error_count": (
                comparison_result.get(
                    "error_count",
                    len(errors)
                )
            ),

            "summary": (
                comparison_result.get(
                    "summary",
                    {}
                )
            ),
        }


        return report


    # ========================================================
    # LEGACY / DIRECT FILE MODE
    # ========================================================

    if not master_file:

        raise ValueError(
            "Either project_id or master_file "
            "must be provided."
        )

    if not os.path.exists(
        master_file
    ):

        raise FileNotFoundError(
            f"Master Word file not found: "
            f"{master_file}"
        )

    master_extension = (
        os.path.splitext(
            master_file
        )[1].lower()
    )

    if master_extension != ".docx":

        raise ValueError(
            "Master Word file must be a .docx file."
        )


    print(
        "📄 Using direct Master DOCX comparison mode."
    )


    # --------------------------------------------------------
    # Rule Engine
    # --------------------------------------------------------

    comparison_result = compare_word_files(

        master_filepath=master_file,

        student_filepath=student_file,
    )


    # --------------------------------------------------------
    # Get errors
    # --------------------------------------------------------

    errors = comparison_result.get(
        "errors",
        []
    )

    if not isinstance(
        errors,
        list
    ):
        errors = []


    # --------------------------------------------------------
    # Generate complete report
    # --------------------------------------------------------

    report = generate_word_report(

        errors=errors,

        student_name=student_name,

        attendance_number=(
            attendance_number
        ),

        grade=grade,

        project_id=project_id,

        master_file=master_file,

        student_file=student_file,

        include_ai=include_ai,

        ai_model=ai_model,
    )


    # --------------------------------------------------------
    # Add comparison information
    # --------------------------------------------------------

    report["comparison"] = {

        "success": bool(
            comparison_result.get(
                "success",
                True
            )
        ),

        "mode": "direct_master_file",

        "master_file": (
            comparison_result.get(
                "master_file",
                master_file
            )
        ),

        "student_file": (
            comparison_result.get(
                "student_file",
                student_file
            )
        ),

        "error_count": (
            comparison_result.get(
                "error_count",
                len(errors)
            )
        ),
    }


    return report


# ============================================================
# SAVE REPORT
# ============================================================

def save_word_report(
    report: Dict[str, Any],
    output_path: str,
) -> str:
    """
    Save report as JSON.
    """

    output_directory = os.path.dirname(
        output_path
    )

    if output_directory:

        os.makedirs(
            output_directory,
            exist_ok=True
        )


    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=4,
        )

    return output_path


# ============================================================
# PRINT REPORT
# ============================================================

def print_word_report(
    report: Dict[str, Any]
):

    print()
    print("=" * 70)
    print("WORD PROJECT GRADING REPORT")
    print("=" * 70)


    # --------------------------------------------------------
    # Student
    # --------------------------------------------------------

    student = report.get(
        "student",
        {}
    )

    print()
    print("STUDENT")
    print("-" * 70)

    print(
        f"Name: "
        f"{student.get('student_name') or 'N/A'}"
    )

    print(
        f"Attendance Number: "
        f"{student.get('attendance_number') or 'N/A'}"
    )

    print(
        f"Grade: "
        f"{student.get('grade') or 'N/A'}"
    )

    print(
        f"Project ID: "
        f"{student.get('project_id') or 'N/A'}"
    )


    # --------------------------------------------------------
    # Files
    # --------------------------------------------------------

    files = report.get(
        "files",
        {}
    )

    print()
    print("FILES")
    print("-" * 70)

    print(
        f"Master: "
        f"{files.get('master_file') or 'Stored Master Rules'}"
    )

    print(
        f"Student: "
        f"{files.get('student_file') or 'N/A'}"
    )


    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    score = report.get(
        "score",
        {}
    )

    print()
    print("RESULT")
    print("-" * 70)

    print(
        f"Score: "
        f"{score.get('score', 0)}/"
        f"{score.get('max_score', MAX_SCORE)}"
    )

    print(
        f"Status: "
        f"{score.get('status', 'FAILED')}"
    )

    print(
        f"Passed: "
        f"{score.get('passed', False)}"
    )

    print(
        f"Points Lost: "
        f"{score.get('points_lost', 0)}"
    )


    # --------------------------------------------------------
    # Category deductions
    # --------------------------------------------------------

    category_deductions = report.get(
        "category_deductions",
        {}
    )

    print()
    print("CATEGORY DEDUCTIONS")
    print("-" * 70)

    if category_deductions:

        for category, deduction in (
            category_deductions.items()
        ):

            print(
                f"{category:<20} -{deduction}"
            )

    else:

        print(
            "No deductions."
        )


    # --------------------------------------------------------
    # Feedback
    # --------------------------------------------------------

    feedback = report.get(
        "feedback",
        []
    )

    print()
    print("STUDENT FEEDBACK")
    print("-" * 70)

    if not feedback:

        print(
            "Excellent! All checked Word document "
            "requirements were satisfied."
        )

    else:

        for index, item in enumerate(
            feedback,
            start=1
        ):

            print()

            print(
                f"{index}. "
                f"{item.get('title', 'Requirement')}"
            )

            print(
                f"   Message: "
                f"{item.get('message', '')}"
            )

            print(
                f"   Why: "
                f"{item.get('reason', '')}"
            )

            print(
                f"   What to do: "
                f"{item.get('correction', '')}"
            )

            print(
                f"   Points lost: "
                f"-{item.get('marks_lost', 0)}"
            )

            if item.get(
                "context_text"
            ):

                print(
                    f"   Details: "
                    f"{item['context_text']}"
                )


    # --------------------------------------------------------
    # AI Feedback
    # --------------------------------------------------------

    ai = report.get(
        "ai",
        {}
    )

    print()
    print("AI FEEDBACK")
    print("-" * 70)

    if ai.get(
        "available",
        False
    ):

        print(
            ai.get(
                "feedback",
                ""
            )
        )

    else:

        print(
            "AI feedback is unavailable. "
            "Deterministic feedback is still available."
        )


    # --------------------------------------------------------
    # Comparison
    # --------------------------------------------------------

    comparison = report.get(
        "comparison",
        {}
    )

    print()
    print("COMPARISON")
    print("-" * 70)

    print(
        f"Mode: "
        f"{comparison.get('mode', 'N/A')}"
    )

    if comparison.get(
        "project_id"
    ):

        print(
            f"Project ID: "
            f"{comparison.get('project_id')}"
        )

    print(
        f"Errors Found: "
        f"{comparison.get('error_count', 0)}"
    )


    print()
    print("=" * 70)
    print("REPORT COMPLETE")
    print("=" * 70)
    print()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    base_directory = os.path.dirname(
        os.path.abspath(__file__)
    )

    master_file = os.path.join(
        base_directory,
        "master_project.docx"
    )

    student_file = os.path.join(
        base_directory,
        "student_project.docx"
    )

    project_id = "1"


    # ========================================================
    # TEST 1
    # Create Master JSON
    # ========================================================

    if os.path.exists(
        master_file
    ):

        try:

            print()
            print(
                "Creating Word Master rules..."
            )

            master_result = (
                create_word_master_project(
                    master_file=master_file,
                    project_id=project_id,
                )
            )

            print(
                "✅ Master rules created."
            )

            print(
                f"Path: "
                f"{master_result.get('master_rules_path')}"
            )

        except Exception as error:

            print()
            print(
                "❌ Master creation error:"
            )

            print(
                str(error)
            )

    else:

        print(
            f"⚠️ Master file not found:\n"
            f"{master_file}"
        )


    # ========================================================
    # TEST 2
    # Grade Student
    # ========================================================

    if os.path.exists(
        student_file
    ):

        try:

            report = grade_word_files(

                student_file=student_file,

                student_name="Test Student",

                attendance_number="34",

                grade="10A",

                project_id=project_id,

                include_ai=True,
            )

            print_word_report(
                report
            )


            # ------------------------------------------------
            # Save JSON report
            # ------------------------------------------------

            report_file = os.path.join(
                base_directory,
                "word_grading_report.json"
            )

            save_word_report(
                report,
                report_file
            )

            print(
                f"JSON report saved to:\n"
                f"{report_file}"
            )

        except Exception as error:

            print()
            print(
                "❌ Student grading error:"
            )

            print(
                str(error)
            )

    else:

        print(
            f"⚠️ Student file not found:\n"
            f"{student_file}"
        )