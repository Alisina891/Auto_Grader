# ============================================================
# WORD SCORING ENGINE
# ============================================================
#
# Purpose:
#   Convert Word Rule Engine errors into a final score.
#
# Important:
#   - Maximum score = 20
#   - Passing score = 12
#   - Font size is NEVER scored
#   - One logical problem should not cause duplicate deductions
#   - This file calculates scores only
#   - Student-friendly explanations belong in word_feedback_engine.py
#
# Flow:
#
#   Word Analyzer
#        ↓
#   Word Rule Engine
#        ↓
#   Word Scoring Engine
#        ↓
#   Word Feedback Engine
#
# ============================================================


# ============================================================
# SCORE SETTINGS
# ============================================================

MAX_SCORE = 20
PASSING_SCORE = 12


# ============================================================
# STATUS SETTINGS
# ============================================================

STATUS_EXCELLENT = "EXCELLENT"
STATUS_VERY_GOOD = "VERY GOOD"
STATUS_GOOD = "GOOD"
STATUS_PASSED = "PASSED"
STATUS_FAILED = "FAILED"


# ============================================================
# ERROR WEIGHTS
# ============================================================
#
# These values represent the maximum points that each
# individual error type can deduct.
#
# Font size intentionally does NOT exist here.
#
# ============================================================

ERROR_WEIGHTS = {

    # --------------------------------------------------------
    # Document / Structure
    # --------------------------------------------------------

    "empty_document": 20,

    "missing_title": 1,

    "missing_heading": 1,

    "wrong_heading_structure": 1,

    "missing_section": 1,

    "missing_content": 1,


    # --------------------------------------------------------
    # Tables
    # --------------------------------------------------------

    "missing_table": 2,

    "wrong_table_structure": 1,

    "missing_table_column": 1,

    "missing_table_row": 1,


    # --------------------------------------------------------
    # Images / Shapes
    # --------------------------------------------------------

    "missing_image": 1,

    "missing_shape": 1,


    # --------------------------------------------------------
    # Formatting
    # --------------------------------------------------------

    "wrong_font": 1,

    "missing_bold": 1,

    "missing_italic": 1,

    "missing_underline": 1,

    "missing_alignment": 1,


    # --------------------------------------------------------
    # Content
    # --------------------------------------------------------

    "missing_required_text": 1,

    "wrong_required_text": 1,


    # --------------------------------------------------------
    # Formatting that we intentionally do NOT score
    # --------------------------------------------------------

    "wrong_font_size": 0,
    "font_size_mismatch": 0,
}


# ============================================================
# ERROR CATEGORIES
# ============================================================

ERROR_CATEGORIES = {

    # Document structure
    "empty_document": "structure",
    "missing_title": "structure",
    "missing_heading": "structure",
    "wrong_heading_structure": "structure",
    "missing_section": "structure",

    # Content
    "missing_content": "content",
    "missing_required_text": "content",
    "wrong_required_text": "content",

    # Tables
    "missing_table": "tables",
    "wrong_table_structure": "tables",
    "missing_table_column": "tables",
    "missing_table_row": "tables",

    # Visual elements
    "missing_image": "visual",
    "missing_shape": "visual",

    # Formatting
    "wrong_font": "formatting",
    "missing_bold": "formatting",
    "missing_italic": "formatting",
    "missing_underline": "formatting",
    "missing_alignment": "formatting",

    # Never scored
    "wrong_font_size": "ignored",
    "font_size_mismatch": "ignored",
}


# ============================================================
# CATEGORY CAPS
# ============================================================
#
# These prevent one area of the document from destroying
# the entire score.
#
# Example:
#
# If there are many formatting problems, formatting cannot
# deduct more than 5 points.
#
# These can be changed later according to your projects.
#
# ============================================================

CATEGORY_MAX_DEDUCTIONS = {

    "structure": 7,

    "content": 6,

    "tables": 5,

    "visual": 3,

    "formatting": 5,
}


# ============================================================
# ERROR TYPES THAT SHOULD ONLY DEDUCT ONCE
# ============================================================
#
# Example:
#
# If five headings are missing, we don't want:
#
#   missing_heading → -5
#
# Instead:
#
#   missing_heading → -1
#
# The Rule Engine can still report all missing headings
# in the message.
#
# ============================================================

ERROR_TYPE_MAX_DEDUCTIONS = {

    "missing_heading": 1,

    "missing_title": 1,

    "missing_section": 1,

    "missing_content": 1,

    "missing_required_text": 1,

    "missing_table_column": 1,

    "missing_table_row": 1,

    "missing_image": 1,

    "missing_shape": 1,
}


# ============================================================
# IGNORED ERROR TYPES
# ============================================================
#
# These errors may be reported by the Rule Engine, but they
# must never reduce the score.
#
# ============================================================

IGNORED_ERROR_TYPES = {

    "wrong_font_size",

    "font_size_mismatch",
}


# ============================================================
# CATEGORY HELPERS
# ============================================================

def get_error_category(error_type):
    """
    Return the category for an error type.
    """

    return ERROR_CATEGORIES.get(
        error_type,
        "other"
    )


def get_error_weight(error_type):
    """
    Return the configured weight for an error type.

    Unknown errors have a default weight of 1.
    """

    return ERROR_WEIGHTS.get(
        error_type,
        1
    )


# ============================================================
# STATUS
# ============================================================

def get_score_status(score):
    """
    Convert a numeric score into a status.
    """

    if score >= 18:
        return STATUS_EXCELLENT

    if score >= 16:
        return STATUS_VERY_GOOD

    if score >= 14:
        return STATUS_GOOD

    if score >= PASSING_SCORE:
        return STATUS_PASSED

    return STATUS_FAILED


# ============================================================
# PASS / FAIL
# ============================================================

def is_passed(score):
    """
    Return True if the student passed.
    """

    return score >= PASSING_SCORE


# ============================================================
# ERROR TYPE HELPER
# ============================================================

def get_error_type(error):
    """
    Support both:

        error["error_type"]

    and older/general:

        error["type"]

    This makes the scoring engine more robust.
    """

    return (
        error.get("error_type")
        or error.get("type")
        or "unknown"
    )


# ============================================================
# ERROR MESSAGE HELPER
# ============================================================

def get_error_message(error):
    """
    Safely get the error message.
    """

    return (
        error.get("message")
        or error.get("error")
        or "Unknown Word document problem."
    )


# ============================================================
# DUPLICATE PROTECTION
# ============================================================

def _should_skip_duplicate(
    error_type,
    already_deducted
):
    """
    Determine whether an error type has already received
    its allowed deduction.

    This prevents repeated deductions for the same logical
    problem.
    """

    if error_type not in ERROR_TYPE_MAX_DEDUCTIONS:
        return False

    maximum = ERROR_TYPE_MAX_DEDUCTIONS[error_type]

    current = already_deducted.get(
        error_type,
        0
    )

    return current >= maximum


# ============================================================
# MAIN SCORE CALCULATION
# ============================================================

def calculate_score(errors, starting_score=MAX_SCORE):
    """
    Calculate the final Word document score.

    Parameters
    ----------
    errors:
        List of errors generated by word_rule_engine.py

    starting_score:
        Normally 20.

    Returns
    -------
    int
        Final score.
    """

    details = _calculate_breakdown(
        errors,
        starting_score
    )

    return details["final_score"]


# ============================================================
# SCORE BREAKDOWN
# ============================================================

def _calculate_breakdown(
    errors,
    starting_score=MAX_SCORE
):
    """
    Internal scoring function.

    Returns detailed scoring information.
    """

    if errors is None:
        errors = []


    # --------------------------------------------------------
    # Make sure starting score is valid
    # --------------------------------------------------------

    try:
        starting_score = float(starting_score)
    except (TypeError, ValueError):
        starting_score = MAX_SCORE


    starting_score = min(
        MAX_SCORE,
        max(0, starting_score)
    )


    # --------------------------------------------------------
    # Normalize errors
    # --------------------------------------------------------

    valid_errors = []

    for error in errors:

        if not isinstance(error, dict):
            continue

        valid_errors.append(error)


    # --------------------------------------------------------
    # Empty document
    # --------------------------------------------------------
    #
    # If the document is empty, it receives zero.
    #
    # We return immediately so other errors don't create
    # additional unnecessary deductions.
    #
    # --------------------------------------------------------

    has_empty_document = any(
        get_error_type(error) == "empty_document"
        for error in valid_errors
    )

    if has_empty_document:

        return {
            "starting_score": starting_score,
            "total_deduction": starting_score,
            "final_score": 0,
            "status": STATUS_FAILED,
            "passed": False,
            "error_count": len(valid_errors),
            "category_deductions": {
                "structure": starting_score
            },
            "error_deductions": {},
            "applied_errors": [],
            "ignored_errors": [],
        }


    # --------------------------------------------------------
    # No errors
    # --------------------------------------------------------

    if not valid_errors:

        final_score = int(
            round(starting_score)
        )

        return {
            "starting_score": starting_score,
            "total_deduction": 0,
            "final_score": final_score,
            "status": get_score_status(final_score),
            "passed": is_passed(final_score),
            "error_count": 0,
            "category_deductions": {},
            "error_deductions": {},
            "applied_errors": [],
            "ignored_errors": [],
        }


    # --------------------------------------------------------
    # Tracking
    # --------------------------------------------------------

    category_deductions = {}

    error_deductions = {}

    already_deducted = {}

    applied_errors = []

    ignored_errors = []


    # --------------------------------------------------------
    # Process errors
    # --------------------------------------------------------

    for error in valid_errors:

        error_type = get_error_type(error)

        category = (
            error.get("category")
            or get_error_category(error_type)
        )

        message = get_error_message(error)


        # ----------------------------------------------------
        # Ignore font size
        # ----------------------------------------------------

        if error_type in IGNORED_ERROR_TYPES:

            ignored_errors.append({
                "error_type": error_type,
                "category": category,
                "message": message,
                "reason": "Font size is intentionally not scored.",
            })

            continue


        # ----------------------------------------------------
        # Ignore explicit zero-weight errors
        # ----------------------------------------------------

        configured_weight = get_error_weight(
            error_type
        )

        if configured_weight <= 0:

            ignored_errors.append({
                "error_type": error_type,
                "category": category,
                "message": message,
                "reason": "This error has zero scoring weight.",
            })

            continue


        # ----------------------------------------------------
        # Duplicate protection
        # ----------------------------------------------------

        if _should_skip_duplicate(
            error_type,
            already_deducted
        ):

            ignored_errors.append({
                "error_type": error_type,
                "category": category,
                "message": message,
                "reason": "Duplicate logical error.",
            })

            continue


        # ----------------------------------------------------
        # Determine requested deduction
        # ----------------------------------------------------

        requested_deduction = error.get(
            "weight",
            configured_weight
        )

        try:
            requested_deduction = float(
                requested_deduction
            )
        except (TypeError, ValueError):

            requested_deduction = configured_weight


        requested_deduction = max(
            0,
            requested_deduction
        )


        # ----------------------------------------------------
        # Error-type cap
        # ----------------------------------------------------

        if error_type in ERROR_TYPE_MAX_DEDUCTIONS:

            maximum_for_type = (
                ERROR_TYPE_MAX_DEDUCTIONS[
                    error_type
                ]
            )

            already_for_type = (
                already_deducted.get(
                    error_type,
                    0
                )
            )

            remaining_for_type = max(
                0,
                maximum_for_type - already_for_type
            )

            requested_deduction = min(
                requested_deduction,
                remaining_for_type
            )


        # ----------------------------------------------------
        # Category cap
        # ----------------------------------------------------

        category_cap = CATEGORY_MAX_DEDUCTIONS.get(
            category
        )

        current_category_deduction = (
            category_deductions.get(
                category,
                0
            )
        )


        if category_cap is not None:

            remaining_category = max(
                0,
                category_cap - current_category_deduction
            )

            requested_deduction = min(
                requested_deduction,
                remaining_category
            )


        # ----------------------------------------------------
        # If nothing remains, ignore
        # ----------------------------------------------------

        if requested_deduction <= 0:

            ignored_errors.append({
                "error_type": error_type,
                "category": category,
                "message": message,
                "reason": "Scoring cap already reached.",
            })

            continue


        # ----------------------------------------------------
        # Apply deduction
        # ----------------------------------------------------

        deduction = requested_deduction


        category_deductions[category] = (
            category_deductions.get(
                category,
                0
            )
            + deduction
        )


        error_deductions[error_type] = (
            error_deductions.get(
                error_type,
                0
            )
            + deduction
        )


        already_deducted[error_type] = (
            already_deducted.get(
                error_type,
                0
            )
            + deduction
        )


        applied_errors.append({
            "error_type": error_type,
            "category": category,
            "message": message,
            "deduction": deduction,
        })


    # --------------------------------------------------------
    # Calculate final score
    # --------------------------------------------------------

    total_deduction = sum(
        category_deductions.values()
    )


    final_score = (
        starting_score
        - total_deduction
    )


    # Never allow negative score
    final_score = max(
        0,
        final_score
    )


    # Round to integer because the project uses whole points
    final_score = int(
        round(final_score)
    )


    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    return {
        "starting_score": int(
            round(starting_score)
        ),

        "total_deduction": int(
            round(total_deduction)
        ),

        "final_score": final_score,

        "status": get_score_status(
            final_score
        ),

        "passed": is_passed(
            final_score
        ),

        "error_count": len(
            valid_errors
        ),

        "category_deductions": {
            category: int(
                round(value)
            )
            for category, value
            in category_deductions.items()
        },

        "error_deductions": {
            error_type: int(
                round(value)
            )
            for error_type, value
            in error_deductions.items()
        },

        "applied_errors": applied_errors,

        "ignored_errors": ignored_errors,
    }


# ============================================================
# PUBLIC DETAILS FUNCTION
# ============================================================

def get_score_details(
    errors,
    starting_score=MAX_SCORE
):
    """
    Return complete scoring information.

    This is the function that the API/reporting layer should
    normally use.
    """

    return _calculate_breakdown(
        errors,
        starting_score
    )


# ============================================================
# PRINT SCORE BREAKDOWN
# ============================================================

def print_score_breakdown(
    errors,
    starting_score=MAX_SCORE
):
    """
    Print a readable scoring report for testing.
    """

    details = get_score_details(
        errors,
        starting_score
    )


    print()
    print("=" * 60)
    print("WORD SCORE BREAKDOWN")
    print("=" * 60)


    print(
        f"Starting Score : "
        f"{details['starting_score']}/20"
    )

    print(
        f"Total Deduction: "
        f"-{details['total_deduction']}"
    )

    print(
        f"Final Score    : "
        f"{details['final_score']}/20"
    )

    print(
        f"Status         : "
        f"{details['status']}"
    )

    print(
        f"Passed         : "
        f"{details['passed']}"
    )


    # --------------------------------------------------------
    # Category deductions
    # --------------------------------------------------------

    print()
    print("CATEGORY DEDUCTIONS")
    print("-" * 60)


    if details["category_deductions"]:

        for category, deduction in (
            details["category_deductions"].items()
        ):

            print(
                f"{category:<20} -{deduction}"
            )

    else:

        print("No deductions.")


    # --------------------------------------------------------
    # Applied errors
    # --------------------------------------------------------

    print()
    print("APPLIED ERRORS")
    print("-" * 60)


    if details["applied_errors"]:

        for index, error in enumerate(
            details["applied_errors"],
            start=1
        ):

            print(
                f"{index}. "
                f"[{error['category']}] "
                f"{error['error_type']} "
                f"(-{error['deduction']})"
            )

            print(
                f"   {error['message']}"
            )

    else:

        print("No errors affected the score.")


    # --------------------------------------------------------
    # Ignored errors
    # --------------------------------------------------------

    print()
    print("IGNORED ERRORS")
    print("-" * 60)


    if details["ignored_errors"]:

        for index, error in enumerate(
            details["ignored_errors"],
            start=1
        ):

            print(
                f"{index}. "
                f"{error['error_type']} "
                f"→ {error['reason']}"
            )

    else:

        print("None.")


    print("=" * 60)
    print()


# ============================================================
# SIMPLE TEST
# ============================================================

if __name__ == "__main__":

    # Example errors coming from word_rule_engine.py

    test_errors = [

        {
            "error_type": "missing_heading",
            "category": "structure",
            "message": "Two required sections are missing.",
        },

        {
            "error_type": "missing_table",
            "category": "tables",
            "message": "One required table is missing.",
        },

        {
            "error_type": "missing_image",
            "category": "visual",
            "message": "One required image is missing.",
        },

        {
            "error_type": "wrong_font",
            "category": "formatting",
            "message": "The required font is missing.",
        },

        {
            "error_type": "wrong_font_size",
            "category": "formatting",
            "message": "Font size differs from the master document.",
        },

    ]


    print_score_breakdown(
        test_errors
    )