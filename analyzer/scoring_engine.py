# ============================================================
# SCORING ENGINE
# ============================================================
#
# Maximum project score = 20
#
# Rule Engine:
#     Detects WHAT is wrong
#
# Scoring Engine:
#     Decides HOW MANY points should be removed
#
# Feedback Engine:
#     Explains the problem to the student
#
# ============================================================


# ============================================================
# MAXIMUM PROJECT SCORE
# ============================================================

MAX_SCORE = 20


# ============================================================
# PASSING SCORE
# ============================================================

PASSING_SCORE = 12


# ============================================================
# ERROR WEIGHTS
# ============================================================

ERROR_WEIGHTS = {

    # --------------------------------------------------------
    # WORKBOOK / SHEET STRUCTURE
    # --------------------------------------------------------

    "empty_project": 20,

    "sheet_count_mismatch": 3,
    "missing_sheet": 4,
    "extra_sheet": 1,

    # --------------------------------------------------------
    # COLUMNS
    # --------------------------------------------------------
    #
    # IMPORTANT:
    #
    # Missing columns are treated as ONE logical problem.
    #
    # Example:
    #
    # 6 missing columns
    #       ↓
    # maximum deduction = 1
    #
    # --------------------------------------------------------

    "column_count_mismatch": 0,
    "missing_column": 1,

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------
    #
    # missing_data is currently used by Rule Engine for
    # insufficient student rows.
    #
    # The Rule Engine also gives this error an explicit
    # weight of 1.
    #
    # --------------------------------------------------------

    "missing_data": 1,
    "wrong_data_type": 1,

    # --------------------------------------------------------
    # FORMULAS
    # --------------------------------------------------------

    "missing_formula": 2,
    "wrong_formula": 2,
    "formula_count_mismatch": 1,
    "extra_formula": 1,

    # --------------------------------------------------------
    # TABLES
    # --------------------------------------------------------

    "missing_table": 2,
    "wrong_table": 1,

    # --------------------------------------------------------
    # DATA VALIDATION
    # --------------------------------------------------------

    "missing_data_validation": 1,

    # --------------------------------------------------------
    # CONDITIONAL FORMATTING
    # --------------------------------------------------------

    "missing_conditional_formatting": 1,

    # --------------------------------------------------------
    # FORMATTING
    # --------------------------------------------------------
    #
    # Column width is intentionally DISABLED.
    #
    # It must NEVER reduce the score.
    #
    # --------------------------------------------------------

    "wrong_column_width": 0,
    "missing_merged_cell": 1,
}


# ============================================================
# ERROR CATEGORIES
# ============================================================

ERROR_CATEGORIES = {

    "structure": {
        "sheet_count_mismatch",
        "missing_sheet",
        "extra_sheet",
    },

    "columns": {
        "column_count_mismatch",
        "missing_column",
    },

    "data": {
        "missing_data",
        "wrong_data_type",
    },

    "formulas": {
        "missing_formula",
        "wrong_formula",
        "formula_count_mismatch",
        "extra_formula",
    },

    "tables": {
        "missing_table",
        "wrong_table",
    },

    "validation": {
        "missing_data_validation",
    },

    "formatting": {
        "missing_conditional_formatting",
        "missing_merged_cell",
    },

}


# ============================================================
# IGNORED ERROR TYPES
# ============================================================
#
# These errors can NEVER affect the score.
#
# This is an additional safety layer.
#
# Even if an old Rule Engine accidentally creates a
# wrong_column_width error, the score will not decrease.
#
# ============================================================

IGNORED_ERROR_TYPES = {

    "wrong_column_width",

}


# ============================================================
# MAXIMUM DEDUCTION PER ERROR TYPE
# ============================================================
#
# These limits apply across the whole project.
#
# Therefore:
#
# 10 missing columns
#       ↓
# maximum = -1
#
# 50 missing rows
#       ↓
# maximum = -1
#
# ============================================================

ERROR_TYPE_MAX_DEDUCTIONS = {

    "missing_column": 1,

    "missing_data": 1,

}


# ============================================================
# CATEGORY MAXIMUM DEDUCTIONS
# ============================================================

CATEGORY_MAX_DEDUCTIONS = {

    "structure": 20,

    "columns": 10,

    "data": 10,

    "formulas": 10,

    "tables": 8,

    "validation": 5,

    "formatting": 5,

}


# ============================================================
# GET ERROR CATEGORY
# ============================================================

def get_error_category(error_type):

    """
    Return the category of an error.
    """

    for category, error_types in ERROR_CATEGORIES.items():

        if error_type in error_types:

            return category

    return "other"


# ============================================================
# INTERNAL SCORE CALCULATION
# ============================================================

def _calculate_breakdown(
    errors,
    starting_score=MAX_SCORE
):

    """
    Internal function used by both calculate_score()
    and get_score_details().

    All scoring logic is centralized here.
    """

    # --------------------------------------------------------
    # Safety
    # --------------------------------------------------------

    if starting_score > MAX_SCORE:

        starting_score = MAX_SCORE

    if starting_score < 0:

        starting_score = 0


    # --------------------------------------------------------
    # Empty project
    # --------------------------------------------------------

    for error in errors:

        if error.get("type") == "empty_project":

            return {

                "starting_score":
                    starting_score,

                "total_deduction":
                    starting_score,

                "final_score":
                    0,

                "status":
                    "FAILED",

                "error_count":
                    len(errors),

                "category_deductions": {

                    "structure":
                        starting_score

                },

                "error_deductions": [

                    {

                        "type":
                            "empty_project",

                        "category":
                            "structure",

                        "deduction":
                            starting_score,

                        "description":
                            "Empty project"

                    }

                ]

            }


    # --------------------------------------------------------
    # No errors
    # --------------------------------------------------------

    if not errors:

        return {

            "starting_score":
                starting_score,

            "total_deduction":
                0,

            "final_score":
                starting_score,

            "status":
                get_score_status(
                    starting_score
                ),

            "error_count":
                0,

            "category_deductions":
                {},

            "error_deductions":
                []

        }


    # --------------------------------------------------------
    # Tracking
    # --------------------------------------------------------

    category_deductions = {}

    error_type_deductions = {}

    error_deductions = []

    total_deduction = 0


    # ========================================================
    # PROCESS ERRORS
    # ========================================================

    for index, error in enumerate(
        errors,
        start=1
    ):

        error_type = error.get(
            "type",
            "unknown"
        )


        # ----------------------------------------------------
        # IGNORE COLUMN WIDTH COMPLETELY
        # ----------------------------------------------------

        if error_type in IGNORED_ERROR_TYPES:

            error_deductions.append({

                "number":
                    index,

                "type":
                    error_type,

                "category":
                    get_error_category(
                        error_type
                    ),

                "weight":
                    0,

                "deduction":
                    0,

                "ignored":
                    True,

                "reason":
                    "This error type is ignored by the scoring engine.",

                "sheet":
                    error.get("sheet"),

                "column":
                    error.get("column"),

                "cell":
                    error.get("cell"),

                "table":
                    error.get("table"),

            })

            continue


        # ----------------------------------------------------
        # TABLE NAME ERRORS ARE NEVER VALID
        # ----------------------------------------------------
        #
        # This protects the system even if an old version of
        # Rule Engine creates a table-name mismatch error.
        #
        # Different table names are allowed.
        #
        # ----------------------------------------------------

        if (
            error_type == "wrong_table"
            and
            error.get("problem") == "name"
        ):

            error_deductions.append({

                "number":
                    index,

                "type":
                    error_type,

                "category":
                    "tables",

                "weight":
                    0,

                "deduction":
                    0,

                "ignored":
                    True,

                "reason":
                    "Table names are not compared.",

                "sheet":
                    error.get("sheet"),

                "column":
                    error.get("column"),

                "cell":
                    error.get("cell"),

                "table":
                    error.get("table"),

            })

            continue


        # ----------------------------------------------------
        # GET WEIGHT
        # ----------------------------------------------------

        try:

            configured_weight = (
                error.get("weight")
            )

            if configured_weight is not None:

                weight = float(
                    configured_weight
                )

            else:

                weight = float(
                    ERROR_WEIGHTS.get(
                        error_type,
                        1
                    )
                )

        except (
            TypeError,
            ValueError
        ):

            weight = float(
                ERROR_WEIGHTS.get(
                    error_type,
                    1
                )
            )


        # ----------------------------------------------------
        # ZERO-WEIGHT ERROR
        # ----------------------------------------------------

        if weight <= 0:

            deduction = 0

            category = get_error_category(
                error_type
            )

            error_deductions.append({

                "number":
                    index,

                "type":
                    error_type,

                "category":
                    category,

                "weight":
                    weight,

                "deduction":
                    deduction,

                "sheet":
                    error.get("sheet"),

                "column":
                    error.get("column"),

                "cell":
                    error.get("cell"),

                "table":
                    error.get("table"),

            })

            continue


        # ----------------------------------------------------
        # ERROR CATEGORY
        # ----------------------------------------------------

        category = get_error_category(
            error_type
        )


        # ----------------------------------------------------
        # CATEGORY DEDUCTION
        # ----------------------------------------------------

        current_category_deduction = (
            category_deductions.get(
                category,
                0
            )
        )

        category_limit = (
            CATEGORY_MAX_DEDUCTIONS.get(
                category,
                MAX_SCORE
            )
        )

        remaining_category = (
            category_limit
            -
            current_category_deduction
        )


        if remaining_category <= 0:

            deduction = 0

        else:

            deduction = min(
                weight,
                remaining_category
            )


        # ----------------------------------------------------
        # SPECIAL ERROR TYPE LIMIT
        # ----------------------------------------------------
        #
        # Example:
        #
        # missing_column #1 -> -1
        # missing_column #2 -> -0
        # missing_column #3 -> -0
        #
        # Therefore the entire project loses only ONE point
        # for missing columns.
        #
        # Same logic applies to missing_data / rows.
        #
        # ----------------------------------------------------

        type_limit = (
            ERROR_TYPE_MAX_DEDUCTIONS.get(
                error_type
            )
        )

        if type_limit is not None:

            current_type_deduction = (
                error_type_deductions.get(
                    error_type,
                    0
                )
            )

            remaining_type = (
                type_limit
                -
                current_type_deduction
            )

            if remaining_type <= 0:

                deduction = 0

            else:

                deduction = min(
                    deduction,
                    remaining_type
                )


        # ----------------------------------------------------
        # UPDATE CATEGORY
        # ----------------------------------------------------

        category_deductions[category] = (
            current_category_deduction
            +
            deduction
        )


        # ----------------------------------------------------
        # UPDATE ERROR TYPE
        # ----------------------------------------------------

        error_type_deductions[error_type] = (
            error_type_deductions.get(
                error_type,
                0
            )
            +
            deduction
        )


        # ----------------------------------------------------
        # UPDATE TOTAL
        # ----------------------------------------------------

        total_deduction += deduction


        # ----------------------------------------------------
        # STORE DETAILS
        # ----------------------------------------------------

        error_deductions.append({

            "number":
                index,

            "type":
                error_type,

            "category":
                category,

            "weight":
                weight,

            "deduction":
                deduction,

            "sheet":
                error.get("sheet"),

            "column":
                error.get("column"),

            "cell":
                error.get("cell"),

            "table":
                error.get("table"),

        })


    # ========================================================
    # FINAL SCORE
    # ========================================================

    final_score = (
        starting_score
        -
        total_deduction
    )


    final_score = max(
        0,
        final_score
    )


    final_score = min(
        MAX_SCORE,
        final_score
    )


    final_score = round(
        final_score,
        2
    )


    # ========================================================
    # RETURN
    # ========================================================

    return {

        "starting_score":
            starting_score,

        "total_deduction":
            round(
                total_deduction,
                2
            ),

        "final_score":
            final_score,

        "status":
            get_score_status(
                final_score
            ),

        "error_count":
            len(errors),

        "category_deductions":
            category_deductions,

        "error_deductions":
            error_deductions

    }


# ============================================================
# CALCULATE SCORE
# ============================================================

def calculate_score(
    errors,
    starting_score=MAX_SCORE
):

    """
    Return only the final score.
    """

    breakdown = _calculate_breakdown(
        errors,
        starting_score
    )

    return breakdown[
        "final_score"
    ]


# ============================================================
# SCORE STATUS
# ============================================================

def get_score_status(score):

    if score >= 18:

        return "EXCELLENT"

    elif score >= 16:

        return "VERY GOOD"

    elif score >= 14:

        return "GOOD"

    elif score >= PASSING_SCORE:

        return "PASSED"

    else:

        return "FAILED"


# ============================================================
# SCORE DETAILS
# ============================================================

def get_score_details(
    errors,
    starting_score=MAX_SCORE
):

    """
    Return complete scoring information.
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

    details = get_score_details(
        errors,
        starting_score
    )


    print()
    print("=" * 60)
    print("                 SCORE BREAKDOWN")
    print("=" * 60)


    print(
        f"\nStarting Score: "
        f"{details['starting_score']}/20"
    )


    # --------------------------------------------------------
    # Individual deductions
    # --------------------------------------------------------

    if details["error_deductions"]:

        print("\nDeductions:")

        for item in details[
            "error_deductions"
        ]:

            ignored_text = ""

            if item.get(
                "ignored",
                False
            ):

                ignored_text = " [IGNORED]"


            print(
                f"  {item['number']}. "
                f"{item['type']} "
                f"({item['category']}): "
                f"-{item['deduction']}"
                f"{ignored_text}"
            )

    else:

        print("\nNo deductions.")


    # --------------------------------------------------------
    # Category deductions
    # --------------------------------------------------------

    if details[
        "category_deductions"
    ]:

        print(
            "\nCategory Deductions:"
        )

        for (
            category,
            deduction
        ) in details[
            "category_deductions"
        ].items():

            print(
                f"  {category}: "
                f"-{deduction}"
            )


    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print(
        f"\nTotal Deduction: "
        f"-{details['total_deduction']}"
    )

    print(
        f"Final Score: "
        f"{details['final_score']}/20"
    )

    print(
        f"Status: "
        f"{details['status']}"
    )

    print("=" * 60)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("SCORING ENGINE TEST")
    print("=" * 60)


    # ========================================================
    # TEST 1 — PERFECT
    # ========================================================

    errors = []

    score = calculate_score(
        errors
    )

    print(
        "\nTEST 1: Perfect Project"
    )

    print(
        f"Score: {score}/20"
    )


    # ========================================================
    # TEST 2 — ONE MISSING COLUMN
    # ========================================================

    errors = [

        {
            "type":
                "missing_column",

            "sheet":
                "Sheet1",

            "column":
                "نام پدر"

        }

    ]

    score = calculate_score(
        errors
    )

    print(
        "\nTEST 2: One Missing Column"
    )

    print(
        f"Score: {score}/20"
    )


    # ========================================================
    # TEST 3 — MANY MISSING COLUMNS
    # ========================================================

    errors = [

        {
            "type":
                "missing_column",

            "sheet":
                "Sheet1",

            "column":
                "Column 1"

        },

        {
            "type":
                "missing_column",

            "sheet":
                "Sheet1",

            "column":
                "Column 2"

        },

        {
            "type":
                "missing_column",

            "sheet":
                "Sheet1",

            "column":
                "Column 3"

        },

        {
            "type":
                "missing_column",

            "sheet":
                "Sheet1",

            "column":
                "Column 4"

        },

        {
            "type":
                "missing_column",

            "sheet":
                "Sheet1",

            "column":
                "Column 5"

        },

        {
            "type":
                "missing_column",

            "sheet":
                "Sheet1",

            "column":
                "Column 6"

        }

    ]

    score = calculate_score(
        errors
    )

    print(
        "\nTEST 3: Six Missing Columns"
    )

    print(
        f"Score: {score}/20"
    )

    assert score == 19


    # ========================================================
    # TEST 4 — MANY MISSING ROWS
    # ========================================================

    errors = [

        {
            "type":
                "missing_data",

            "sheet":
                "Sheet1",

            "expected_rows":
                100,

            "actual_rows":
                20

        },

        {
            "type":
                "missing_data",

            "sheet":
                "Sheet2",

            "expected_rows":
                100,

            "actual_rows":
                20

        }

    ]

    score = calculate_score(
        errors
    )

    print(
        "\nTEST 4: Missing Rows"
    )

    print(
        f"Score: {score}/20"
    )

    assert score == 19


    # ========================================================
    # TEST 5 — COLUMN WIDTH
    # ========================================================

    errors = [

        {
            "type":
                "wrong_column_width",

            "sheet":
                "Sheet1",

            "column":
                "Name",

            "expected":
                20,

            "actual":
                5

        }

    ]

    score = calculate_score(
        errors
    )

    print(
        "\nTEST 5: Wrong Column Width"
    )

    print(
        f"Score: {score}/20"
    )

    assert score == 20


    # ========================================================
    # TEST 6 — TABLE NAME
    # ========================================================

    errors = [

        {
            "type":
                "wrong_table",

            "sheet":
                "Sheet1",

            "table":
                "Table1",

            "problem":
                "name",

            "expected":
                "Table1",

            "actual":
                "MyStudentTable"

        }

    ]

    score = calculate_score(
        errors
    )

    print(
        "\nTEST 6: Different Table Name"
    )

    print(
        f"Score: {score}/20"
    )

    assert score == 20


    # ========================================================
    # TEST 7 — CURRENT STUDENT EXAMPLE
    # ========================================================

    errors = [

        {
            "type":
                "column_count_mismatch",

            "sheet":
                "Sheet2"

        },

        {
            "type":
                "missing_data",

            "sheet":
                "Sheet2",

            "expected_rows":
                16,

            "actual_rows":
                10

        },

        {
            "type":
                "missing_column",

            "sheet":
                "Sheet2",

            "column":
                "اسم محصول"

        },

        {
            "type":
                "missing_column",

            "sheet":
                "Sheet2",

            "column":
                "ماه اول"

        },

        {
            "type":
                "missing_column",

            "sheet":
                "Sheet2",

            "column":
                "ماه دوم"

        },

        {
            "type":
                "missing_column",

            "sheet":
                "Sheet2",

            "column":
                "ماه سوم"

        },

        {
            "type":
                "missing_column",

            "sheet":
                "Sheet2",

            "column":
                "چهارم"

        },

        {
            "type":
                "missing_column",

            "sheet":
                "Sheet2",

            "column":
                "پنجم"

        },

        {
            "type":
                "wrong_table",

            "sheet":
                "Sheet2",

            "table":
                "Table2",

            "problem":
                "name"

        }

    ]


    print(
        "\nTEST 7: Current Student Example"
    )

    print_score_breakdown(
        errors
    )


    details = get_score_details(
        errors
    )

    # 20
    # -1 missing rows
    # -1 missing columns
    # -0 column count
    # -0 table name
    #
    # = 18

    assert details[
        "final_score"
    ] == 18


    print(
        "\n✅ ALL SCORING TESTS PASSED"
    )