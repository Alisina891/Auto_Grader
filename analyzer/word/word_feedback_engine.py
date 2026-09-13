# ============================================================
# WORD FEEDBACK ENGINE
# ============================================================
#
# Purpose:
#   Convert Word scoring results into clear student-friendly
#   feedback.
#
# Important:
#   - This file DOES NOT calculate the score.
#   - word_scoring_engine.py is responsible for scoring.
#   - This file uses the deductions already calculated by
#     the scoring engine.
#   - Font size is never presented as a scoring problem.
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
#        ↓
#   Student Report
#
# ============================================================


from analyzer.word.word_scoring_engine import (
    get_score_details,
    get_score_status,
    MAX_SCORE,
    PASSING_SCORE,
)


# ============================================================
# FEEDBACK INFORMATION
# ============================================================

FEEDBACK_MESSAGES = {

    # --------------------------------------------------------
    # Structure
    # --------------------------------------------------------

    "missing_title": {
        "title": "Title is missing",
        "reason": (
            "The document should contain the required title "
            "or title section."
        ),
        "correction": (
            "Add a clear title that represents the main topic "
            "of the document."
        ),
        "severity": "medium",
    },

    "missing_heading": {
        "title": "Required section is missing",
        "reason": (
            "Some required sections or headings from the "
            "project structure were not found."
        ),
        "correction": (
            "Review the project instructions and add the "
            "missing sections."
        ),
        "severity": "medium",
    },

    "wrong_heading_structure": {
        "title": "Section structure needs adjustment",
        "reason": (
            "The document contains headings, but their "
            "structure does not match the required organization."
        ),
        "correction": (
            "Organize the sections using the required heading "
            "levels and document structure."
        ),
        "severity": "medium",
    },

    "missing_section": {
        "title": "Required section is missing",
        "reason": (
            "A required part of the document was not found."
        ),
        "correction": (
            "Add the missing section and include its required "
            "content."
        ),
        "severity": "medium",
    },


    # --------------------------------------------------------
    # Content
    # --------------------------------------------------------

    "missing_content": {
        "title": "Required content is missing",
        "reason": (
            "A required part of the document does not contain "
            "the expected content."
        ),
        "correction": (
            "Add the required information to the appropriate "
            "section."
        ),
        "severity": "medium",
    },

    "missing_required_text": {
        "title": "Required text is missing",
        "reason": (
            "The project contains specific text or information "
            "that should appear in the document."
        ),
        "correction": (
            "Add the required text or information to the "
            "appropriate location."
        ),
        "severity": "medium",
    },

    "wrong_required_text": {
        "title": "Required text needs correction",
        "reason": (
            "Some specifically required content does not match "
            "the project requirement."
        ),
        "correction": (
            "Check the project instructions and correct the "
            "required content."
        ),
        "severity": "medium",
    },


    # --------------------------------------------------------
    # Tables
    # --------------------------------------------------------

    "missing_table": {
        "title": "Required table is missing",
        "reason": (
            "The project requires one or more tables, but a "
            "required table was not found."
        ),
        "correction": (
            "Add the required table to the document."
        ),
        "severity": "high",
    },

    "wrong_table_structure": {
        "title": "Table structure needs adjustment",
        "reason": (
            "A table exists, but its required structure is "
            "different from the project requirement."
        ),
        "correction": (
            "Check the required number of rows and columns and "
            "adjust the table structure."
        ),
        "severity": "medium",
    },

    "missing_table_column": {
        "title": "Required table column is missing",
        "reason": (
            "A required table column was not found."
        ),
        "correction": (
            "Add the required column to the table."
        ),
        "severity": "medium",
    },

    "missing_table_row": {
        "title": "Required table row is missing",
        "reason": (
            "A required table row was not found."
        ),
        "correction": (
            "Add the required row to the table."
        ),
        "severity": "medium",
    },


    # --------------------------------------------------------
    # Images
    # --------------------------------------------------------

    "missing_image": {
        "title": "Required image is missing",
        "reason": (
            "The project requires an image, but the required "
            "image element was not found."
        ),
        "correction": (
            "Add the required image to the document."
        ),
        "severity": "medium",
    },


    # --------------------------------------------------------
    # Shapes
    # --------------------------------------------------------

    "missing_shape": {
        "title": "Required shape is missing",
        "reason": (
            "The project requires a shape or drawing element "
            "that was not found."
        ),
        "correction": (
            "Add the required shape or drawing element."
        ),
        "severity": "medium",
    },


    # --------------------------------------------------------
    # Formatting
    # --------------------------------------------------------

    "wrong_font": {
        "title": "Font formatting needs adjustment",
        "reason": (
            "The document uses a font that does not match the "
            "required font setting."
        ),
        "correction": (
            "Use the font required by the project instructions."
        ),
        "severity": "low",
    },

    "missing_bold": {
        "title": "Bold formatting is missing",
        "reason": (
            "Some required text should use bold formatting."
        ),
        "correction": (
            "Apply bold formatting to the required text."
        ),
        "severity": "low",
    },

    "missing_italic": {
        "title": "Italic formatting is missing",
        "reason": (
            "Some required text should use italic formatting."
        ),
        "correction": (
            "Apply italic formatting to the required text."
        ),
        "severity": "low",
    },

    "missing_underline": {
        "title": "Underline formatting is missing",
        "reason": (
            "Some required text should use underline formatting."
        ),
        "correction": (
            "Apply underline formatting to the required text."
        ),
        "severity": "low",
    },

    "missing_alignment": {
        "title": "Text alignment needs adjustment",
        "reason": (
            "Some required content does not use the expected "
            "alignment."
        ),
        "correction": (
            "Adjust the alignment according to the project "
            "requirements."
        ),
        "severity": "low",
    },


    # --------------------------------------------------------
    # Unknown
    # --------------------------------------------------------

    "unknown": {
        "title": "Document requirement needs attention",
        "reason": (
            "A document requirement was not fully satisfied."
        ),
        "correction": (
            "Review the project instructions and check the "
            "document carefully."
        ),
        "severity": "medium",
    },
}


# ============================================================
# ERROR TYPE
# ============================================================

def get_error_type(error):
    """
    Support both the Word format:

        error_type

    and the general/older format:

        type
    """

    return (
        error.get("error_type")
        or error.get("type")
        or "unknown"
    )


# ============================================================
# ERROR MESSAGE
# ============================================================

def get_error_message(error):
    """
    Safely return the original Rule Engine message.
    """

    return (
        error.get("message")
        or error.get("error")
        or ""
    )


# ============================================================
# FEEDBACK TEMPLATE
# ============================================================

def get_feedback_template(error_type):
    """
    Return the predefined feedback information for an error.
    """

    return FEEDBACK_MESSAGES.get(
        error_type,
        FEEDBACK_MESSAGES["unknown"]
    )


# ============================================================
# CONTEXT
# ============================================================

def get_error_context(error):
    """
    Extract useful context from a Rule Engine error.

    The Rule Engine may provide extra information such as:

        section
        heading
        table
        expected
        actual
        image
        shape

    We don't require these fields, but if they exist,
    they can be included in the feedback.
    """

    context = {}

    possible_fields = [
        "section",
        "heading",
        "table",
        "table_index",
        "expected",
        "actual",
        "expected_count",
        "actual_count",
        "expected_columns",
        "actual_columns",
        "image",
        "image_index",
        "shape",
        "shape_index",
        "font",
        "expected_font",
        "actual_font",
    ]

    for field in possible_fields:

        if field in error:

            value = error[field]

            if value is not None:

                context[field] = value

    return context


# ============================================================
# CONTEXT TEXT
# ============================================================

def format_context(context):
    """
    Convert technical context into a small readable sentence.
    """

    if not context:
        return ""


    parts = []


    # Section
    if context.get("section"):

        parts.append(
            f"Section: {context['section']}"
        )


    # Heading
    if context.get("heading"):

        parts.append(
            f"Heading: {context['heading']}"
        )


    # Table
    if context.get("table"):

        parts.append(
            f"Table: {context['table']}"
        )


    # Table index
    elif context.get("table_index") is not None:

        parts.append(
            f"Table: {context['table_index']}"
        )


    # Expected / actual
    if (
        context.get("expected") is not None
        and context.get("actual") is not None
    ):

        parts.append(
            f"Expected: {context['expected']}, "
            f"Found: {context['actual']}"
        )


    # Expected count / actual count
    elif (
        context.get("expected_count") is not None
        and context.get("actual_count") is not None
    ):

        parts.append(
            f"Expected: {context['expected_count']}, "
            f"Found: {context['actual_count']}"
        )


    # Columns
    if (
        context.get("expected_columns") is not None
        and context.get("actual_columns") is not None
    ):

        parts.append(
            f"Expected columns: "
            f"{context['expected_columns']}, "
            f"Found: "
            f"{context['actual_columns']}"
        )


    # Font
    if context.get("expected_font"):

        parts.append(
            f"Required font: "
            f"{context['expected_font']}"
        )

    elif context.get("font"):

        parts.append(
            f"Font: {context['font']}"
        )


    return " | ".join(
        str(part)
        for part in parts
    )


# ============================================================
# SINGLE FEEDBACK ITEM
# ============================================================

def create_feedback_item(
    error,
    deduction=0
):
    """
    Convert one applied scoring error into a student-friendly
    feedback item.

    deduction MUST come from the scoring engine.
    """

    error_type = get_error_type(error)

    template = get_feedback_template(
        error_type
    )

    original_message = get_error_message(
        error
    )

    context = get_error_context(
        error
    )

    context_text = format_context(
        context
    )


    # --------------------------------------------------------
    # Main message
    # --------------------------------------------------------

    if original_message:

        message = original_message

    else:

        message = template["title"]


    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    result = {

        "error_type": error_type,

        "category": (
            error.get("category")
            or "other"
        ),

        "title": template["title"],

        "message": message,

        "reason": template["reason"],

        "correction": template["correction"],

        "marks_lost": int(
            round(deduction)
        ),

        "severity": template["severity"],
    }


    # Add context only if available
    if context:

        result["context"] = context

    if context_text:

        result["context_text"] = context_text


    return result


# ============================================================
# MAIN FEEDBACK FUNCTION
# ============================================================

def generate_feedback(
    errors,
    score_details=None
):
    """
    Generate student-friendly feedback.

    IMPORTANT:
    If score_details is provided, only errors that actually
    caused a deduction are included as scored feedback.

    This guarantees that the feedback and score stay
    synchronized.
    """

    if errors is None:

        errors = []


    # --------------------------------------------------------
    # Get score details
    # --------------------------------------------------------

    if score_details is None:

        score_details = get_score_details(
            errors
        )


    applied_errors = (
        score_details.get(
            "applied_errors",
            []
        )
    )


    feedback = []


    # --------------------------------------------------------
    # Use ONLY applied errors
    # --------------------------------------------------------

    for applied_error in applied_errors:

        deduction = applied_error.get(
            "deduction",
            0
        )


        # Safety check
        if deduction <= 0:

            continue


        item = create_feedback_item(
            applied_error,
            deduction
        )


        feedback.append(
            item
        )


    return feedback


# ============================================================
# SCORE SUMMARY
# ============================================================

def generate_score_summary(
    errors,
    score_details=None
):
    """
    Generate a summary using the actual scoring engine result.

    This function DOES NOT independently calculate deductions.
    """

    if score_details is None:

        score_details = get_score_details(
            errors
        )


    return {

        "score": score_details[
            "final_score"
        ],

        "max_score": MAX_SCORE,

        "status": score_details[
            "status"
        ],

        "passed": score_details[
            "passed"
        ],

        "total_deduction": score_details[
            "total_deduction"
        ],

        "error_count": score_details[
            "error_count"
        ],

        "category_deductions": (
            score_details[
                "category_deductions"
            ]
        ),
    }


# ============================================================
# COMPLETE STUDENT REPORT
# ============================================================

def generate_student_report(errors):
    """
    Generate one complete Word grading report.

    This is useful for the API.
    """

    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    score_details = get_score_details(
        errors
    )


    # --------------------------------------------------------
    # Feedback
    # --------------------------------------------------------

    feedback = generate_feedback(
        errors,
        score_details
    )


    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = generate_score_summary(
        errors,
        score_details
    )


    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    return {

        "success": True,

        "score": summary["score"],

        "max_score": summary["max_score"],

        "status": summary["status"],

        "passed": summary["passed"],

        "total_deduction": (
            summary["total_deduction"]
        ),

        "error_count": (
            summary["error_count"]
        ),

        "category_deductions": (
            summary["category_deductions"]
        ),

        "feedback": feedback,

        "scoring": score_details,
    }


# ============================================================
# PRINT STUDENT FEEDBACK
# ============================================================

def print_student_feedback(errors):
    """
    Print a readable report during development/testing.
    """

    report = generate_student_report(
        errors
    )


    print()
    print("=" * 70)
    print("WORD STUDENT REPORT")
    print("=" * 70)


    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    print(
        f"Score: "
        f"{report['score']}/"
        f"{report['max_score']}"
    )

    print(
        f"Status: "
        f"{report['status']}"
    )

    print(
        f"Passed: "
        f"{report['passed']}"
    )


    # --------------------------------------------------------
    # Deduction
    # --------------------------------------------------------

    print(
        f"Points Lost: "
        f"{report['total_deduction']}"
    )


    # --------------------------------------------------------
    # Feedback
    # --------------------------------------------------------

    print()
    print("FEEDBACK")
    print("-" * 70)


    if not report["feedback"]:

        print(
            "Excellent! All required Word document "
            "requirements were satisfied."
        )

    else:

        for index, item in enumerate(
            report["feedback"],
            start=1
        ):

            print()
            print(
                f"{index}. {item['title']}"
            )

            print(
                f"   Message: "
                f"{item['message']}"
            )

            print(
                f"   Why: "
                f"{item['reason']}"
            )

            print(
                f"   What to do: "
                f"{item['correction']}"
            )

            print(
                f"   Points lost: "
                f"-{item['marks_lost']}"
            )

            if item.get("context_text"):

                print(
                    f"   Details: "
                    f"{item['context_text']}"
                )


    print()
    print("=" * 70)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_errors = [

        {
            "error_type": "missing_heading",
            "category": "structure",
            "message": (
                "2 required heading(s) are missing."
            ),
        },

        {
            "error_type": "missing_table",
            "category": "tables",
            "message": (
                "1 required table(s) are missing."
            ),
        },

        {
            "error_type": "missing_image",
            "category": "visual",
            "message": (
                "1 required image(s) are missing."
            ),
        },

        {
            "error_type": "wrong_font",
            "category": "formatting",
            "message": (
                "Required font is not being used."
            ),
        },

        {
            "error_type": "wrong_font_size",
            "category": "formatting",
            "message": (
                "Font size does not match."
            ),
        },
    ]


    print_student_feedback(
        test_errors
    )