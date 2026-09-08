
# ============================================================
# REPORT GENERATOR
# ============================================================

import json
import os
from datetime import datetime


REPORTS_FOLDER = "reports"
MAX_SCORE = 20


# ============================================================
# CREATE REPORT
# ============================================================

def generate_report(result, student_name, project_id):
    """
    Create a complete report from the Rule Engine result.

    The grading system is based on a maximum score of 20.
    """

    # --------------------------------------------------------
    # Basic information
    # --------------------------------------------------------

    total_checks = result.get(
        "total_checks",
        0
    )

    checks_passed = result.get(
        "checks_passed",
        0
    )

    score = result.get(
        "score",
        0
    )

    # Keep score inside 0-20
    score = max(
        0,
        min(MAX_SCORE, score)
    )

    # --------------------------------------------------------
    # Calculate accuracy
    # --------------------------------------------------------

    if total_checks > 0:

        accuracy = round(
            (checks_passed / total_checks) * 100,
            1
        )

    else:

        accuracy = 0.0

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    status = result.get(
        "status"
    )

    if not status:

        status = (
            "PASSED"
            if result.get("passed", False)
            else "FAILED"
        )

    # --------------------------------------------------------
    # Score breakdown
    # --------------------------------------------------------

    score_breakdown = result.get(
        "score_breakdown",
        result.get(
            "score_details",
            {}
        )
    )

    # Make sure score breakdown is consistent
    starting_score = score_breakdown.get(
        "starting_score",
        MAX_SCORE
    )

    total_deduction = score_breakdown.get(
        "total_deduction",
        MAX_SCORE - score
    )

    final_score = score_breakdown.get(
        "final_score",
        score
    )

    category_deductions = score_breakdown.get(
        "category_deductions",
        {}
    )

    error_deductions = score_breakdown.get(
        "error_deductions",
        []
    )

    # --------------------------------------------------------
    # Student feedback
    # --------------------------------------------------------

    student_feedback = result.get(
        "student_feedback",
        []
    )

    # --------------------------------------------------------
    # Create complete report
    # --------------------------------------------------------

    report = {

        # ----------------------------------------------------
        # Student information
        # ----------------------------------------------------

        "student": student_name,

        "project": project_id,

        # ----------------------------------------------------
        # Score
        # ----------------------------------------------------

        "score": final_score,

        "max_score": MAX_SCORE,

        "status": status,

        # ----------------------------------------------------
        # Accuracy
        # ----------------------------------------------------

        "accuracy": accuracy,

        # ----------------------------------------------------
        # Checks
        # ----------------------------------------------------

        "total_checks": total_checks,

        "checks_passed": checks_passed,

        # ----------------------------------------------------
        # Score breakdown
        # ----------------------------------------------------

        "score_breakdown": {

            "starting_score": starting_score,

            "total_deduction": total_deduction,

            "final_score": final_score,

            "status": status,

            "category_deductions": (
                category_deductions
            ),

            "error_deductions": (
                error_deductions
            )

        },

        # ----------------------------------------------------
        # Feedback
        # ----------------------------------------------------

        "feedback": result.get(
            "feedback",
            []
        ),

        "student_feedback": (
            student_feedback
        ),

        # ----------------------------------------------------
        # Detected errors
        # ----------------------------------------------------

        "errors": result.get(
            "errors",
            []
        ),

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        "summary": result.get(
            "summary",
            ""
        ),

        # ----------------------------------------------------
        # Detailed information
        # ----------------------------------------------------

        "details": {

            "total_checks": total_checks,

            "checks_passed": checks_passed,

            "accuracy": accuracy,

            "starting_score": starting_score,

            "final_score": final_score,

            "max_score": MAX_SCORE,

            "total_deduction": total_deduction,

            "status": status,

            "error_count": len(
                result.get(
                    "errors",
                    []
                )
            )

        },

        # ----------------------------------------------------
        # Timestamp
        # ----------------------------------------------------

        "generated_at": (
            datetime.now().isoformat()
        )

    }

    return report


# ============================================================
# SAVE REPORT AS JSON
# ============================================================

def save_report_json(
    report,
    student_name,
    project_id
):
    """
    Save report as a JSON file.
    """

    os.makedirs(
        REPORTS_FOLDER,
        exist_ok=True
    )

    safe_student_name = (
        student_name
        .replace(" ", "_")
    )

    filename = (
        f"{project_id}_"
        f"{safe_student_name}.json"
    )

    filepath = os.path.join(
        REPORTS_FOLDER,
        filename
    )

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            report,
            f,
            ensure_ascii=False,
            indent=2
        )

    return filepath


# ============================================================
# PRINT REPORT
# ============================================================

def print_report(report):
    """
    Print a human-readable report.
    """

    print()
    print("=" * 60)
    print("                 PROJECT REPORT")
    print("=" * 60)

    # --------------------------------------------------------
    # Student
    # --------------------------------------------------------

    print(
        f"Student: {report['student']}"
    )

    print(
        f"Project: {report['project']}"
    )

    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    print(
        f"Score: "
        f"{report['score']}/"
        f"{report['max_score']}"
    )

    print(
        f"Status: {report['status']}"
    )

    print(
        f"Accuracy: "
        f"{report['accuracy']}%"
    )

    print(
        f"Checks: "
        f"{report['checks_passed']}/"
        f"{report['total_checks']}"
    )

    print("-" * 60)

    # --------------------------------------------------------
    # Score Breakdown
    # --------------------------------------------------------

    breakdown = report.get(
        "score_breakdown",
        {}
    )

    print(
        "SCORE BREAKDOWN:"
    )

    print()

    print(
        f"  Starting Score: "
        f"{breakdown.get('starting_score', MAX_SCORE)}/"
        f"{report['max_score']}"
    )

    print()

    category_deductions = breakdown.get(
        "category_deductions",
        {}
    )

    if category_deductions:

        print(
            "  Category Deductions:"
        )

        for category, deduction in (
            category_deductions.items()
        ):

            print(
                f"    {category.capitalize():<20}"
                f"-{deduction}"
            )

    print()

    print(
        f"  Total Deduction: "
        f"-{breakdown.get('total_deduction', 0)}"
    )

    print(
        f"  Final Score: "
        f"{breakdown.get('final_score', report['score'])}/"
        f"{report['max_score']}"
    )

    print(
        f"  Status: "
        f"{breakdown.get('status', report['status'])}"
    )

    print("-" * 60)

    # --------------------------------------------------------
    # Errors
    # --------------------------------------------------------

    if report["errors"]:

        print(
            "ERRORS FOUND:"
        )

        for index, error in enumerate(
            report["errors"],
            start=1
        ):

            error_type = error.get(
                "type",
                "unknown"
            )

            sheet = error.get(
                "sheet"
            )

            if sheet:

                print(
                    f"  {index}. ❌ "
                    f"{error_type} "
                    f"[{sheet}]"
                )

            else:

                print(
                    f"  {index}. ❌ "
                    f"{error_type}"
                )

    else:

        print(
            "ERRORS FOUND:"
        )

        print(
            "  ✅ No errors found."
        )

    print("-" * 60)

    # --------------------------------------------------------
    # Student Feedback
    # --------------------------------------------------------

    if report["student_feedback"]:

        print(
            "STUDENT FEEDBACK:"
        )

        for index, item in enumerate(
            report["student_feedback"],
            start=1
        ):

            severity = item.get(
                "severity",
                "info"
            ).upper()

            title = item.get(
                "title",
                "Feedback"
            )

            message = item.get(
                "message",
                ""
            )

            reason = item.get(
                "reason",
                ""
            )

            correction = item.get(
                "correction",
                ""
            )

            marks_lost = item.get(
                "marks_lost",
                0
            )

            print()

            print(
                f"{index}. [{severity}] "
                f"{title}"
            )

            print(
                f"   Problem: "
                f"{message}"
            )

            if reason:

                print(
                    f"   Why: "
                    f"{reason}"
                )

            if correction:

                print(
                    f"   Fix: "
                    f"{correction}"
                )

            print(
                f"   Marks Lost: "
                f"-{marks_lost}"
            )

    else:

        print(
            "STUDENT FEEDBACK:"
        )

        print(
            "  ✅ Excellent! "
            "No problems found."
        )

    print("=" * 60)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 60
    )

    print(
        "REPORT GENERATOR TEST"
    )

    print(
        "=" * 60
    )

    # --------------------------------------------------------
    # Fake result from Rule Engine
    # --------------------------------------------------------

    test_result = {

        "score": 15,

        "status": "GOOD",

        "passed": True,

        "total_checks": 10,

        "checks_passed": 8,

        "score_breakdown": {

            "starting_score": 20,

            "total_deduction": 5,

            "final_score": 15,

            "status": "GOOD",

            "category_deductions": {

                "columns": 1,

                "formulas": 2,

                "tables": 2

            },

            "error_deductions": [

                {
                    "type": "missing_column",
                    "deduction": 1
                },

                {
                    "type": "wrong_formula",
                    "deduction": 2
                },

                {
                    "type": "missing_table",
                    "deduction": 2
                }

            ]

        },

        "feedback": [

            "[Sheet1] Missing column: Name",

            "[Sheet1] Wrong formula at H5"

        ],

        "errors": [

            {
                "type": "missing_column",
                "sheet": "Sheet1",
                "column": "Name"
            },

            {
                "type": "wrong_formula",
                "sheet": "Sheet1",
                "cell": "H5"
            },

            {
                "type": "missing_table",
                "sheet": "Sheet2",
                "table": "Table2"
            }

        ],

        "student_feedback": [

            {

                "severity": "error",

                "title": "Missing Column",

                "message": (
                    'The column "Name" '
                    'is missing.'
                ),

                "reason": (
                    "This column is required "
                    "by the Master Project."
                ),

                "correction": (
                    "Add the missing column "
                    "with the exact required name."
                ),

                "marks_lost": 1

            },

            {

                "severity": "error",

                "title": "Wrong Formula",

                "message": (
                    "The formula in H5 "
                    "is incorrect."
                ),

                "reason": (
                    "The formula does not "
                    "match the Master Project."
                ),

                "correction": (
                    "Replace the incorrect "
                    "formula with the required formula."
                ),

                "marks_lost": 2

            }

        ],

        "summary": (
            "Score: 15/20 | "
            "Checks: 8/10"
        )

    }

    # --------------------------------------------------------
    # Generate
    # --------------------------------------------------------

    report = generate_report(
        test_result,
        "Test Student",
        "Project_1"
    )

    # --------------------------------------------------------
    # Print
    # --------------------------------------------------------

    print_report(
        report
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    filepath = save_report_json(
        report,
        "Test Student",
        "Project_1"
    )

    print()

    print(
        f"✅ Report saved to: {filepath}"
    )

