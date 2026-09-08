
import os
import json

from analyzer.excel_analyzer import extract_full_rules

from analyzer.rule_engine import (
    load_master_rules,
    compare_structure,
    generate_report
)


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ID = "Project_1"
STUDENT_NAME = "Test Student"

STUDENT_FILE = "student_project3.xlsx"

# ============================================================
# IMPORTANT:
# The maximum score for every project is 20.
# ============================================================

MAX_SCORE = 20
PASSING_SCORE = 12


# ============================================================
# MAIN GRADER
# ============================================================

def grade_project(student_file, student_name, project_id):
    """
    Complete grading pipeline.

    Excel File
        ↓
    Excel Analyzer
        ↓
    Rule Engine
        ↓
    Scoring Engine
        ↓
    Feedback Engine
        ↓
    Report
    """

    print("=" * 60)
    print("                    AUTO GRADER")
    print("=" * 60)

    print(f"\nStudent: {student_name}")
    print(f"Project: {project_id}")

    # ========================================================
    # CHECK STUDENT FILE
    # ========================================================

    if not os.path.exists(student_file):

        print("\n❌ Student file not found!")
        print(f"File: {student_file}")

        return None

    # ========================================================
    # LOAD MASTER RULES
    # ========================================================

    print("\n[1/4] Loading master rules...")

    master_rules = load_master_rules(project_id)

    if master_rules is None:

        print("❌ Master rules not found!")
        print(f"Project: {project_id}")

        return None

    print("✅ Master rules loaded")

    # ========================================================
    # ANALYZE STUDENT EXCEL
    # ========================================================

    print("\n[2/4] Analyzing student Excel file...")

    try:

        student_rules = extract_full_rules(
            student_file
        )

    except Exception as e:

        print("❌ Excel analysis failed!")
        print(f"Error: {e}")

        return None

    print("✅ Excel analysis complete")

    # ========================================================
    # COMPARE WITH MASTER
    # ========================================================

    print("\n[3/4] Checking project...")

    try:

        result = compare_structure(
            student_rules,
            master_rules
        )

    except Exception as e:

        print("❌ Rule checking failed!")
        print(f"Error: {e}")

        return None

    print("✅ Rule checking complete")

    # ========================================================
    # GENERATE REPORT
    # ========================================================

    print("\n[4/4] Generating report...")

    report = generate_report(
        result,
        student_name,
        project_id
    )

    print("✅ Report generated")

    # ========================================================
    # GET SCORE
    # ========================================================

    score = result.get(
        "score",
        MAX_SCORE
    )

    # Keep score inside 0-20
    score = max(
        0,
        min(
            MAX_SCORE,
            score
        )
    )

    if isinstance(score, float):
        score = round(score, 2)

    # ========================================================
    # GET STATUS
    # ========================================================

    if score >= PASSING_SCORE:

        status = "PASSED"

    else:

        status = "FAILED"

    # ========================================================
    # GET ERRORS
    # ========================================================

    errors = result.get(
        "errors",
        []
    )

    error_count = len(errors)

    # ========================================================
    # GET SCORE BREAKDOWN
    # ========================================================

    score_breakdown = result.get(
        "score_details",
        {}
    )

    total_deduction = score_breakdown.get(
        "total_deduction",
        MAX_SCORE - score
    )

    category_deductions = score_breakdown.get(
        "category_deductions",
        {}
    )

    # ========================================================
    # GET CHECK INFORMATION
    # ========================================================

    total_checks = result.get(
        "total_checks",
        0
    )

    checks_passed = result.get(
        "checks_passed",
        0
    )

    accuracy = report.get(
        "details",
        {}
    ).get(
        "accuracy",
        0
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print("\n" + "=" * 60)
    print("                    FINAL RESULT")
    print("=" * 60)

    print()
    print(f"YOUR SCORE: {score}/{MAX_SCORE}")

    if status == "PASSED":

        print("STATUS: ✅ PASSED")

    else:

        print("STATUS: ❌ FAILED")

    print(
        f"ACCURACY: {accuracy}%"
    )

    print(
        f"ERRORS FOUND: {error_count}"
    )

    print(
        f"TOTAL MARKS LOST: {total_deduction}"
    )

    print(
        f"CHECKS: {checks_passed}/{total_checks}"
    )

    # ========================================================
    # SCORE BREAKDOWN
    # ========================================================

    print("\n" + "-" * 60)
    print("SCORE BREAKDOWN")
    print("-" * 60)

    print(
        f"\nStarting Score: {MAX_SCORE}/{MAX_SCORE}"
    )

    print("\nCategory Deductions:")

    if category_deductions:

        for category, deduction in category_deductions.items():

            print(
                f"  {category.replace('_', ' ').title():<25}"
                f"-{deduction}"
            )

    else:

        print("  No deductions")

    print(
        f"\nTotal Deduction: -{total_deduction}"
    )

    print(
        f"Final Score: {score}/{MAX_SCORE}"
    )

    print(
        f"Status: {status}"
    )

    # ========================================================
    # STUDENT FEEDBACK
    # ========================================================

    print("\n" + "-" * 60)
    print("STUDENT FEEDBACK")
    print("-" * 60)

    student_feedback = result.get(
        "student_feedback",
        []
    )

    if not student_feedback:

        print("\n✅ Excellent!")
        print(
            "No problems were found in your project."
        )

    else:

        print()
        print(
            f"You lost {total_deduction} "
            f"marks because of:"
        )

        for item in student_feedback:

            print()
            print(
                f"[{item.get('severity', 'warning').upper()}] "
                f"{item.get('title', 'Project Issue')}"
            )

            # ------------------------------------------------
            # Problem
            # ------------------------------------------------

            print(
                f"  Problem: "
                f"{item.get('message', '')}"
            )

            # ------------------------------------------------
            # Why
            # ------------------------------------------------

            if item.get("reason"):

                print(
                    f"  Why: "
                    f"{item['reason']}"
                )

            # ------------------------------------------------
            # Fix
            # ------------------------------------------------

            if item.get("correction"):

                print(
                    f"  Fix: "
                    f"{item['correction']}"
                )

            # ------------------------------------------------
            # Marks Lost
            # ------------------------------------------------

            marks_lost = item.get(
                "marks_lost",
                0
            )

            print(
                f"  Marks Lost: -{marks_lost}"
            )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)

    print(
        f"\nYOUR SCORE: {score}/{MAX_SCORE}"
    )

    print(
        f"TOTAL MARKS LOST: {total_deduction}"
    )

    print(
        f"STATUS: "
        f"{'✅ PASSED' if status == 'PASSED' else '❌ FAILED'}"
    )

    print("=" * 60)

    # ========================================================
    # PREPARE REPORT
    # ========================================================

    if isinstance(report, dict):

        # ----------------------------------------------------
        # Main score
        # ----------------------------------------------------

        report["score"] = score

        report["max_score"] = MAX_SCORE

        report["status"] = status

        # ----------------------------------------------------
        # Keep score breakdown
        # ----------------------------------------------------

        report["score_breakdown"] = score_breakdown

        # ----------------------------------------------------
        # Keep complete student feedback
        # ----------------------------------------------------

        report["student_feedback"] = student_feedback

        # ----------------------------------------------------
        # Keep errors
        # ----------------------------------------------------

        report["errors"] = errors

        # ----------------------------------------------------
        # Update details
        # ----------------------------------------------------

        if not isinstance(
            report.get("details"),
            dict
        ):

            report["details"] = {}

        report["details"]["starting_score"] = MAX_SCORE

        report["details"]["final_score"] = score

        report["details"]["max_score"] = MAX_SCORE

        report["details"]["total_deduction"] = (
            total_deduction
        )

        report["details"]["status"] = status

        report["details"]["error_count"] = (
            error_count
        )

        report["details"]["total_checks"] = (
            total_checks
        )

        report["details"]["checks_passed"] = (
            checks_passed
        )

        report["details"]["accuracy"] = (
            accuracy
        )

    # ========================================================
    # SAVE REPORT
    # ========================================================

    reports_folder = "reports"

    os.makedirs(
        reports_folder,
        exist_ok=True
    )

    safe_student_name = (
        student_name
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    report_file = os.path.join(
        reports_folder,
        f"{project_id}_{safe_student_name}.json"
    )

    with open(
        report_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            report,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"\n✅ Complete report saved to: "
        f"{report_file}"
    )

    print("=" * 60)

    return report


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    grade_project(
        student_file=STUDENT_FILE,
        student_name=STUDENT_NAME,
        project_id=PROJECT_ID
    )

