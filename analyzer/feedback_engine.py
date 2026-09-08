
# ============================================================
# FEEDBACK ENGINE
# ============================================================

from analyzer.scoring_engine import (
    MAX_SCORE,
    ERROR_WEIGHTS,
    get_error_category,
    calculate_score,
    get_score_status,
)
from analyzer.ai_feedback import generate_ai_feedback


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_marks_lost(error_type):
    """
    Get the marks lost for a specific error type.

    The weights come directly from scoring_engine.py
    so feedback and scoring always use the same values.
    """
    return ERROR_WEIGHTS.get(error_type, 1)


def get_reason(error_type):
    """
    Explain why the error is wrong.
    """

    reasons = {

        "missing_column":
            "This column is required by the Master Project.",

        "column_count_mismatch":
            "The number of columns in your sheet does not match "
            "the structure required by the Master Project.",

        "missing_data":
            "Required data rows are missing from your project.",

        "wrong_data_type":
            "The type of data in this column does not match "
            "the type required by the Master Project.",

        "missing_formula":
            "A required formula is missing from the specified cell.",

        "wrong_formula":
            "The formula in this cell does not match the formula "
            "required by the Master Project.",

        "extra_formula":
            "This formula was not required by the Master Project.",

        "formula_count_mismatch":
            "The number of formulas does not match the required project structure.",

        "missing_table":
            "A required Excel table is missing from the project.",

        "wrong_table":
            "The table structure does not match the Master Project.",

        "missing_data_validation":
            "A required data validation rule is missing.",

        "missing_conditional_formatting":
            "Required conditional formatting is missing.",

        "wrong_column_width":
            "The column width does not match the required project format.",

        "missing_merged_cell":
            "A required merged cell range is missing.",

        "sheet_count_mismatch":
            "The number of worksheets does not match the Master Project.",

        "missing_sheet":
            "This worksheet is required by the Master Project.",

        "extra_sheet":
            "This worksheet was not required by the Master Project.",
    }

    return reasons.get(
        error_type,
        "This part of the project does not match the requirements "
        "defined in the Master Project."
    )


def get_correction(error_type):
    """
    Give the student a simple correction instruction.
    """

    corrections = {

        "missing_column":
            "Add the missing column with the exact required name.",

        "column_count_mismatch":
            "Check the Master Project and make the number of columns match exactly.",

        "missing_data":
            "Enter the required data rows according to the Master Project.",

        "wrong_data_type":
            "Change the values so their data type matches the Master Project.",

        "missing_formula":
            "Enter the required formula in the specified cell.",

        "wrong_formula":
            "Replace the incorrect formula with the required formula.",

        "extra_formula":
            "Remove the unnecessary formula if it was added by mistake.",

        "formula_count_mismatch":
            "Check the Master Project and make the number of formulas match.",

        "missing_table":
            "Create the required Excel table with the correct structure.",

        "wrong_table":
            "Correct the table name, columns, or structure to match the Master Project.",

        "missing_data_validation":
            "Add the required data validation rule.",

        "missing_conditional_formatting":
            "Add the required conditional formatting.",

        "wrong_column_width":
            "Adjust the column width to match the required format.",

        "missing_merged_cell":
            "Merge the required cell range.",

        "sheet_count_mismatch":
            "Add or remove worksheets so the total matches the Master Project.",

        "missing_sheet":
            "Create the missing worksheet with the required name.",

        "extra_sheet":
            "Remove the unnecessary worksheet if it was added by mistake.",
    }

    return corrections.get(
        error_type,
        "Compare your project with the Master Project and correct this issue."
    )


# ============================================================
# GENERATE STUDENT FEEDBACK
# ============================================================

def generate_feedback(errors):
    """
    Convert structured Rule Engine errors
    into clear student-friendly feedback.

    Every feedback item includes:
    - What happened
    - Why it is wrong
    - How to fix it
    - Marks lost
    """

    feedback = []

    # --------------------------------------------------------
    # PERFECT PROJECT
    # --------------------------------------------------------

    if not errors:

        return [
            {
                "title": "Perfect!",
                "message": "No issues were found in your project.",
                "reason": "Your project matches the Master Project requirements.",
                "correction": "No correction is required.",
                "marks_lost": 0,
                "severity": "success"
            }
        ]

    # --------------------------------------------------------
    # PROCESS EACH ERROR
    # --------------------------------------------------------

    for error in errors:

        error_type = error.get("type")
        sheet = error.get("sheet", "")

        marks_lost = get_marks_lost(error_type)
        reason = get_reason(error_type)
        correction = get_correction(error_type)

        # ====================================================
        # MISSING COLUMN
        # ====================================================

        if error_type == "missing_column":

            column = error.get("column")

            feedback.append({
                "title": "Missing Column",
                "message": (
                    f'The column "{column}" is missing '
                    f'in sheet "{sheet}".'
                ),
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "error",
                "sheet": sheet,
                "column": column
            })

        # ====================================================
        # COLUMN COUNT
        # ====================================================

        elif error_type == "column_count_mismatch":

            expected = error.get("expected")
            actual = error.get("actual")

            feedback.append({
                "title": "Column Count",
                "message": (
                    f'Sheet "{sheet}" should contain '
                    f'{expected} columns, but your file contains '
                    f'{actual} columns.'
                ),
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "error",
                "sheet": sheet
            })

        # ====================================================
        # MISSING DATA
        # ====================================================

        elif error_type == "missing_data":

            expected = error.get("expected_rows")
            actual = error.get("actual_rows")
            missing = error.get("missing_rows")

            feedback.append({
                "title": "Missing Data",
                "message": (
                    f'Sheet "{sheet}" should contain '
                    f'{expected} data rows, but your file contains '
                    f'{actual}. '
                    f'{missing} row(s) are missing.'
                ),
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "error",
                "sheet": sheet
            })

        # ====================================================
        # WRONG DATA TYPE
        # ====================================================

        elif error_type == "wrong_data_type":

            column = error.get("column")
            expected = error.get("expected")
            actual = error.get("actual")

            feedback.append({
                "title": "Wrong Data Type",
                "message": (
                    f'The data type in column "{column}" '
                    f'of sheet "{sheet}" is incorrect. '
                    f'Expected: {expected}. '
                    f'Found: {actual}.'
                ),
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "error",
                "sheet": sheet,
                "column": column
            })

        # ====================================================
        # MISSING FORMULA
        # ====================================================

        elif error_type == "missing_formula":

            cell = error.get("cell")
            expected = error.get("expected")

            if cell:

                message = (
                    f'Sheet "{sheet}" is missing the required '
                    f'formula in cell {cell}. '
                    f'Expected formula: {expected}'
                )

            else:

                count = error.get("expected_count", 0)

                message = (
                    f'Sheet "{sheet}" is missing required formulas. '
                    f'Expected {count} formula(s), but none were found.'
                )

            feedback.append({
                "title": "Missing Formula",
                "message": message,
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "error",
                "sheet": sheet,
                "cell": cell
            })

        # ====================================================
        # WRONG FORMULA
        # ====================================================

        elif error_type == "wrong_formula":

            cell = error.get("cell")
            expected = error.get("expected")
            actual = error.get("actual")

            feedback.append({
                "title": "Wrong Formula",
                "message": (
                    f'The formula in cell {cell} '
                    f'of sheet "{sheet}" is incorrect. '
                    f'Expected: {expected}. '
                    f'Found: {actual}.'
                ),
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "error",
                "sheet": sheet,
                "cell": cell
            })

        # ====================================================
        # EXTRA FORMULA
        # ====================================================

        elif error_type == "extra_formula":

            cell = error.get("cell")

            feedback.append({
                "title": "Extra Formula",
                "message": (
                    f'An unexpected formula was found '
                    f'in cell {cell} of sheet "{sheet}".'
                ),
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "warning",
                "sheet": sheet,
                "cell": cell
            })

        # ====================================================
        # FORMULA COUNT
        # ====================================================

        elif error_type == "formula_count_mismatch":

            expected = error.get("expected")
            actual = error.get("actual")

            feedback.append({
                "title": "Formula Count",
                "message": (
                    f'Sheet "{sheet}" should contain '
                    f'{expected} formulas, but your file contains '
                    f'{actual}.'
                ),
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "error",
                "sheet": sheet
            })

        # ====================================================
        # MISSING TABLE
        # ====================================================

        elif error_type == "missing_table":

            expected = error.get("expected_count")
            actual = error.get("actual_count")

            feedback.append({
                "title": "Missing Table",
                "message": (
                    f'Sheet "{sheet}" should contain '
                    f'{expected} table(s), but your file contains '
                    f'{actual}.'
                ),
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "error",
                "sheet": sheet
            })

        # ====================================================
        # WRONG TABLE
        # ====================================================

        elif error_type == "wrong_table":

            table = error.get("table")
            problem = error.get("problem")
            expected = error.get("expected")
            actual = error.get("actual")

            feedback.append({
                "title": "Table Error",
                "message": (
                    f'Table "{table}" in sheet "{sheet}" '
                    f'has an incorrect {problem}. '
                    f'Expected: {expected}. '
                    f'Found: {actual}.'
                ),
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "error",
                "sheet": sheet,
                "table": table
            })

        # ====================================================
        # DATA VALIDATION
        # ====================================================

        elif error_type == "missing_data_validation":

            expected = error.get("expected_count")
            actual = error.get("actual_count")

            feedback.append({
                "title": "Missing Data Validation",
                "message": (
                    f'Sheet "{sheet}" should contain '
                    f'{expected} data validation rule(s), '
                    f'but only {actual} were found.'
                ),
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "error",
                "sheet": sheet
            })

        # ====================================================
        # CONDITIONAL FORMATTING
        # ====================================================

        elif error_type == "missing_conditional_formatting":

            expected = error.get("expected_count")
            actual = error.get("actual_count")

            feedback.append({
                "title": "Missing Conditional Formatting",
                "message": (
                    f'Sheet "{sheet}" should contain '
                    f'{expected} conditional formatting rule(s), '
                    f'but only {actual} were found.'
                ),
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "error",
                "sheet": sheet
            })

        # ====================================================
        # COLUMN WIDTH
        # ====================================================

        elif error_type == "wrong_column_width":

            column = error.get("column")
            expected = error.get("expected")
            actual = error.get("actual")

            feedback.append({
                "title": "Column Width",
                "message": (
                    f'The width of column "{column}" '
                    f'in sheet "{sheet}" is incorrect. '
                    f'Expected approximately {expected}, '
                    f'but found {actual}.'
                ),
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "warning",
                "sheet": sheet,
                "column": column
            })

        # ====================================================
        # MERGED CELL
        # ====================================================

        elif error_type == "missing_merged_cell":

            cell_range = error.get("range")

            feedback.append({
                "title": "Missing Merged Cell",
                "message": (
                    f'The merged cell range "{cell_range}" '
                    f'is missing from sheet "{sheet}".'
                ),
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "error",
                "sheet": sheet,
                "range": cell_range
            })

        # ====================================================
        # SHEET COUNT
        # ====================================================

        elif error_type == "sheet_count_mismatch":

            expected = error.get("expected")
            actual = error.get("actual")

            feedback.append({
                "title": "Sheet Count",
                "message": (
                    f'The project should contain '
                    f'{expected} sheet(s), but your file contains '
                    f'{actual}.'
                ),
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "error"
            })

        # ====================================================
        # MISSING SHEET
        # ====================================================

        elif error_type == "missing_sheet":

            sheet_name = error.get("sheet")

            feedback.append({
                "title": "Missing Sheet",
                "message": (
                    f'The sheet "{sheet_name}" '
                    f'is missing from your project.'
                ),
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "error",
                "sheet": sheet_name
            })

        # ====================================================
        # EXTRA SHEET
        # ====================================================

        elif error_type == "extra_sheet":

            sheet_name = error.get("sheet")

            feedback.append({
                "title": "Extra Sheet",
                "message": (
                    f'An unexpected sheet "{sheet_name}" '
                    f'was found in your project.'
                ),
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "warning",
                "sheet": sheet_name
            })

        # ====================================================
        # UNKNOWN ERROR
        # ====================================================

        else:

            feedback.append({
                "title": "Project Issue",
                "message": f'An issue was detected: {error}',
                "reason": reason,
                "correction": correction,
                "marks_lost": marks_lost,
                "severity": "warning"
            })

    return feedback



# ============================================================
# AI ENHANCED FEEDBACK
# ============================================================

def generate_ai_enhanced_feedback(errors, score_details):
    """
    Generate deterministic feedback first,
    then use AI only to explain verified results.

    IMPORTANT:
    - Score is NOT calculated by AI.
    - Marks are NOT decided by AI.
    - Errors are NOT decided by AI.
    - AI only explains verified results.
    """

    # --------------------------------------------------------
    # No errors
    # --------------------------------------------------------

    if not errors:

        return {
            "ai_feedback": (
                "هیچ مشکلی در پروژه شما پیدا نشد. آفرین!"
            )
        }

    # --------------------------------------------------------
    # Generate verified deterministic feedback
    # --------------------------------------------------------

    verified_feedback = generate_feedback(errors)

    # --------------------------------------------------------
    # Send errors + VERIFIED deductions to AI
    # --------------------------------------------------------

    ai_feedback = generate_ai_feedback(
        errors,
        score_details.get(
            "error_deductions",
            []
        )
    )

    # --------------------------------------------------------
    # AI unavailable
    # --------------------------------------------------------

    if not ai_feedback:

        return {
            "ai_feedback": None,
            "deterministic_feedback": verified_feedback
        }

    # --------------------------------------------------------
    # Return both
    # --------------------------------------------------------

    return {
        "ai_feedback": ai_feedback,
        "deterministic_feedback": verified_feedback
    }

# ============================================================
# SCORE SUMMARY
# ============================================================

def generate_score_summary(errors):
    """
    Generate a student-friendly score summary.

    Uses the exact same scoring engine as the Rule Engine.
    """

    score = calculate_score(
        errors,
        starting_score=MAX_SCORE
    )

    status = get_score_status(score)

    total_deduction = MAX_SCORE - score

    # Category totals
    category_deductions = {}

    for error in errors:

        error_type = error.get("type")

        marks_lost = get_marks_lost(error_type)

        category = get_error_category(error_type)

        category_deductions[category] = (
            category_deductions.get(category, 0)
            + marks_lost
        )

    return {
        "starting_score": MAX_SCORE,
        "total_deduction": total_deduction,
        "final_score": score,
        "status": status,
        "category_deductions": category_deductions
    }


# ============================================================
# PRINT STUDENT FEEDBACK
# ============================================================

def print_student_feedback(errors):
    """
    Print a complete student-friendly feedback report.
    """

    summary = generate_score_summary(errors)

    print()
    print("=" * 60)
    print("STUDENT FEEDBACK")
    print("=" * 60)

    print()
    print(f"YOUR SCORE: {summary['final_score']}/{MAX_SCORE}")
    print(f"STATUS: {summary['status']}")

    print()
    print(
        f"You lost {summary['total_deduction']} "
        f"marks because of:"
    )

    print()

    for category, deduction in summary["category_deductions"].items():

        print(
            f"  {category.replace('_', ' ').title():<25} "
            f"-{deduction}"
        )

    print()
    print("-" * 60)

    feedback = generate_feedback(errors)

    for index, item in enumerate(feedback, start=1):

        print()
        print(
            f"{index}. [{item['severity'].upper()}] "
            f"{item['title']}"
        )

        print(f"   Problem: {item['message']}")

        print(f"   Why: {item['reason']}")

        print(f"   Fix: {item['correction']}")

        print(f"   Marks Lost: -{item['marks_lost']}")


        # ========================================================
    # AI EXPLANATION
    # ========================================================

    print()
    print("-" * 60)
    print("AI STUDENT EXPLANATION")
    print("-" * 60)

    ai_feedback = generate_ai_feedback(
        errors
    )

    if ai_feedback:

        print()
        print(ai_feedback)

    else:

        print()
        print(
            "AI explanation is currently unavailable."
        )
        print(
            "The verified feedback above is still valid."
        )
    
    print()
    print("=" * 60)
    print(
        f"FINAL SCORE: "
        f"{summary['final_score']}/{MAX_SCORE}"
    )
    print(
        f"TOTAL LOST: "
        f"{summary['total_deduction']}"
    )
    print(
        f"STATUS: "
        f"{summary['status']}"
    )
    print("=" * 60)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_errors = [

        {
            "type": "missing_column",
            "sheet": "Sheet1",
            "column": "نام پدر"
        },

        {
            "type": "wrong_formula",
            "sheet": "Sheet1",
            "cell": "H5",
            "expected": "=SUM(E5:G5)",
            "actual": "=AVERAGE(E5:G5)"
        },

        {
            "type": "missing_formula",
            "sheet": "Sheet2",
            "cell": "D5",
            "expected": "=B5*C5"
        }

    ]

    print("=" * 60)
    print("FEEDBACK ENGINE TEST")
    print("=" * 60)

    feedback = generate_feedback(test_errors)

    print()

    for item in feedback:

        print(f"[{item['severity'].upper()}] {item['title']}")

        print(f"  Problem: {item['message']}")

        print(f"  Why: {item['reason']}")

        print(f"  Fix: {item['correction']}")

        print(f"  Marks Lost: -{item['marks_lost']}")

        print()

    print("-" * 60)

    summary = generate_score_summary(test_errors)

    print(f"Starting Score: {summary['starting_score']}/20")
    print(f"Total Deduction: -{summary['total_deduction']}")
    print(f"Final Score: {summary['final_score']}/20")
    print(f"Status: {summary['status']}")

    print("=" * 60)

