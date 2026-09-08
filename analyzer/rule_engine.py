import json
import os
from collections import Counter

from analyzer.scoring_engine import (
    MAX_SCORE,
    get_score_status,
    get_score_details,
)

from analyzer.feedback_engine import (
    generate_feedback,
    generate_ai_enhanced_feedback,
)

from analyzer.report_generator import save_report_json


MASTER_RULES_FOLDER = "master_rules"

PASSING_SCORE = 12


# ============================================================
# NORMALIZATION
# ============================================================

def _normalize_text(value):

    if value is None:
        return ""

    text = str(value)

    text = (
        text
        .replace("\u200c", "")
        .replace("\u200f", "")
        .replace("\ufeff", "")
    )

    return " ".join(
        text.strip().split()
    ).casefold()


def _normalize_columns(columns):

    return [
        _normalize_text(col)
        for col in (columns or [])
        if _normalize_text(col)
    ]


def _normalize_formula(formula):

    if formula is None:
        return ""

    return (
        str(formula)
        .strip()
        .replace(" ", "")
        .casefold()
    )


# ============================================================
# MASTER RULES
# ============================================================

def save_master_rules(
    rules,
    project_id
):

    os.makedirs(
        MASTER_RULES_FOLDER,
        exist_ok=True
    )

    filename = os.path.join(
        MASTER_RULES_FOLDER,
        f"project_{project_id}.json"
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            rules,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"✅ Master rules saved for Project "
        f"{project_id}"
    )

    return filename


def load_master_rules(
    project_id
):

    filename = os.path.join(
        MASTER_RULES_FOLDER,
        f"project_{project_id}.json"
    )

    if not os.path.exists(
        filename
    ):

        return None

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# COLUMN MATCHING
# ============================================================

def _find_matching_column(
    master_column,
    student_columns
):

    """
    Find a Student column using its logical header.

    Physical Excel position is completely ignored.
    """

    target = _normalize_text(
        master_column
    )

    for student_column in (
        student_columns or []
    ):

        if _normalize_text(
            student_column
        ) == target:

            return student_column

    return None


def _columns_match(
    master_columns,
    student_columns
):

    """
    Compare columns as logical sets.

    Order and physical location do NOT matter.
    """

    master_set = set(
        _normalize_columns(
            master_columns
        )
    )

    student_set = set(
        _normalize_columns(
            student_columns
        )
    )

    return (
        master_set
        ==
        student_set
    )


# ============================================================
# FORMULA MATCHING
# ============================================================

def _get_formula_type(
    formula
):

    formula_type = formula.get(
        "formula_type"
    )

    if formula_type:

        return _normalize_text(
            formula_type
        ).upper()

    return "OTHER"


def _get_formula_functions(
    formula
):

    functions = formula.get(
        "formula_functions"
    )

    if not functions:

        formula_type = _get_formula_type(
            formula
        )

        if formula_type != "OTHER":

            return [formula_type]

        return []

    return [
        str(function).upper()
        for function in functions
    ]


def _formula_has_same_function(
    master_formula,
    student_formula
):

    master_functions = set(
        _get_formula_functions(
            master_formula
        )
    )

    student_functions = set(
        _get_formula_functions(
            student_formula
        )
    )

    if not master_functions:

        return False

    return master_functions.issubset(
        student_functions
    )


def _formula_exact_match(
    master_formula,
    student_formula
):

    return (
        _normalize_formula(
            master_formula.get(
                "formula"
            )
        )
        ==
        _normalize_formula(
            student_formula.get(
                "formula"
            )
        )
    )


def _formula_header_match(
    master_formula,
    student_formula
):

    master_header = _normalize_text(
        master_formula.get(
            "header"
        )
    )

    student_header = _normalize_text(
        student_formula.get(
            "header"
        )
    )

    if not master_header:

        return False

    return (
        master_header
        ==
        student_header
    )


def _formula_matches(
    master_formula,
    student_formula
):

    """
    Flexible formula matching.

    Priority:

        1. Strict location if explicitly required
        2. Exact formula anywhere
        3. Same logical header + function
        4. Same function anywhere
    """

    if not master_formula:

        return False

    if not student_formula:

        return False


    # --------------------------------------------------------
    # Explicit strict location
    # --------------------------------------------------------

    if master_formula.get(
        "location_strict",
        False
    ):

        return (

            master_formula.get(
                "cell_address"
            )
            ==
            student_formula.get(
                "cell_address"
            )

            and

            _formula_exact_match(
                master_formula,
                student_formula
            )

        )


    # --------------------------------------------------------
    # Exact formula anywhere
    # --------------------------------------------------------

    if _formula_exact_match(
        master_formula,
        student_formula
    ):

        return True


    # --------------------------------------------------------
    # Same logical header + same function
    # --------------------------------------------------------

    if (

        _formula_header_match(
            master_formula,
            student_formula
        )

        and

        _formula_has_same_function(
            master_formula,
            student_formula
        )

    ):

        return True


    # --------------------------------------------------------
    # Same function anywhere
    # --------------------------------------------------------

    if _formula_has_same_function(
        master_formula,
        student_formula
    ):

        return True

    return False


def _find_matching_student_formula(
    master_formula,
    student_formulas,
    used_indexes
):

    for index, student_formula in enumerate(
        student_formulas or []
    ):

        if index in used_indexes:

            continue

        if _formula_matches(
            master_formula,
            student_formula
        ):

            return index

    return None


# ============================================================
# FORMULA REQUIREMENTS
# ============================================================

def _build_formula_type_counter(
    formulas
):

    counter = Counter()

    for formula in formulas or []:

        functions = _get_formula_functions(
            formula
        )

        if functions:

            counter[
                functions[0]
            ] += 1

        else:

            counter[
                _get_formula_type(
                    formula
                )
            ] += 1

    return counter


# ============================================================
# TABLE MATCHING
# ============================================================

def _table_columns(
    table
):

    columns = table.get(
        "columns",
        []
    )

    return [
        _normalize_text(col)
        for col in columns
    ]


def _table_structure_matches(
    master_table,
    student_table
):

    """
    Compare the actual table structure.

    IMPORTANT:

    Table NAME is NEVER compared.

    Example:

        Master:  Table1
        Student: StudentTable

    If their required table structure matches,
    the table is considered correct.

    Table location is also flexible unless the Master
    explicitly requests strict location.
    """

    master_columns = _table_columns(
        master_table
    )

    student_columns = _table_columns(
        student_table
    )


    # --------------------------------------------------------
    # Compare logical table columns.
    #
    # Table name is intentionally ignored.
    # --------------------------------------------------------

    if master_columns != student_columns:

        return False


    # --------------------------------------------------------
    # Optional header requirement
    # --------------------------------------------------------

    master_header = master_table.get(
        "show_header"
    )

    student_header = student_table.get(
        "show_header"
    )

    if (

        master_header is not None

        and

        student_header is not None

        and

        master_header != student_header

    ):

        return False


    # --------------------------------------------------------
    # Optional totals requirement
    # --------------------------------------------------------

    master_totals = master_table.get(
        "show_totals"
    )

    student_totals = student_table.get(
        "show_totals"
    )

    if (

        master_totals is not None

        and

        student_totals is not None

        and

        master_totals != student_totals

    ):

        return False


    return True


def _table_location_is_strict(
    master_table
):

    return bool(
        master_table.get(
            "location_strict",
            False
        )
    )


# ============================================================
# MERGED CELL MATCHING
# ============================================================

def _merged_shape(
    range_string
):

    if not range_string:

        return None

    try:

        start, end = (
            range_string.split(":")
        )

        from openpyxl.utils.cell import (
            coordinate_to_tuple
        )

        start_row, start_col = (
            coordinate_to_tuple(
                start
            )
        )

        end_row, end_col = (
            coordinate_to_tuple(
                end
            )
        )

        return (

            end_row - start_row + 1,

            end_col - start_col + 1

        )

    except Exception:

        return None


def _merged_cells_match(
    master_sheet,
    student_sheet
):

    """
    Merged cells are compared by shape,
    not physical address.
    """

    master_cells = master_sheet.get(
        "merged_cells",
        []
    )

    student_cells = student_sheet.get(
        "merged_cells",
        []
    )

    master_shapes = [

        _merged_shape(cell)

        for cell in master_cells

    ]

    student_shapes = [

        _merged_shape(cell)

        for cell in student_cells

    ]

    master_shapes = sorted(
        shape
        for shape in master_shapes
        if shape
    )

    student_shapes = sorted(
        shape
        for shape in student_shapes
        if shape
    )

    return (
        master_shapes
        ==
        student_shapes
    )


# ============================================================
# DATA VALIDATION
# ============================================================

def _validation_signature(
    rule
):

    return (

        _normalize_text(
            rule.get("type")
        ),

        _normalize_text(
            rule.get("operator")
        ),

        _normalize_text(
            rule.get("formula1")
        ),

        _normalize_text(
            rule.get("formula2")
        )

    )


def _validation_matches(
    master_rule,
    student_rule
):

    return (

        _validation_signature(
            master_rule
        )

        ==

        _validation_signature(
            student_rule
        )

    )


# ============================================================
# CONDITIONAL FORMATTING
# ============================================================

def _cf_signature(
    rule
):

    formula = rule.get(
        "formula"
    )

    if isinstance(
        formula,
        list
    ):

        formula = [

            _normalize_text(
                item
            )

            for item in formula

        ]

    else:

        formula = _normalize_text(
            formula
        )

    return (

        _normalize_text(
            rule.get("type")
        ),

        _normalize_text(
            rule.get("operator")
        ),

        str(formula)

    )


def _conditional_formatting_matches(
    master_rule,
    student_rule
):

    return (

        _cf_signature(
            master_rule
        )

        ==

        _cf_signature(
            student_rule
        )

    )


# ============================================================
# SHEET COMPARISON
# ============================================================

def compare_sheets(
    student_sheet,
    master_sheet,
    sheet_name
):

    feedback = []

    errors = []

    checks_passed = 0

    total_checks = 0


    # ========================================================
    # CHECK 1 — LOGICAL COLUMNS
    # ========================================================

    total_checks += 1

    master_columns = master_sheet.get(
        "columns",
        []
    )

    student_columns = student_sheet.get(
        "columns",
        []
    )

    master_column_set = set(
        _normalize_columns(
            master_columns
        )
    )

    student_column_set = set(
        _normalize_columns(
            student_columns
        )
    )

    missing_columns = (
        master_column_set
        -
        student_column_set
    )

    extra_columns = (
        student_column_set
        -
        master_column_set
    )


    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Column position/order is NOT checked.
    #
    # ALL missing columns create ONE error only.
    #
    # Therefore:
    #
    # 1 missing column  -> -1
    # 6 missing columns -> -1
    # 20 missing columns -> -1
    #
    # --------------------------------------------------------

    if not missing_columns:

        checks_passed += 1

    else:

        missing_display = sorted(
            missing_columns
        )

        feedback.append(

            f"[{sheet_name}] Missing required "
            f"columns: "
            f"{', '.join(missing_display)}"

        )

        errors.append({

            "type":
                "missing_column",

            "sheet":
                sheet_name,

            # Keep scalar "column" for compatibility
            # with the existing Feedback Engine.
            "column":
                ", ".join(
                    missing_display
                ),

            # Also preserve structured information.
            "columns":
                missing_display,

            # Explicitly one point.
            "weight":
                1

        })


    # --------------------------------------------------------
    # Extra columns are informational only.
    # --------------------------------------------------------

    if extra_columns:

        feedback.append(

            f"[{sheet_name}] Additional columns "
            f"detected: "
            f"{', '.join(sorted(extra_columns))}"

        )


    # ========================================================
    # CHECK 2 — DATA ROWS
    # ========================================================

    total_checks += 1

    expected_rows = master_sheet.get(
        "data_rows",
        0
    )

    actual_rows = student_sheet.get(
        "data_rows",
        0
    )


    if actual_rows >= expected_rows:

        checks_passed += 1

    else:

        missing_rows = (
            expected_rows
            -
            actual_rows
        )

        feedback.append(

            f"[{sheet_name}] Missing data: "
            f"expected at least "
            f"{expected_rows} rows, "
            f"got {actual_rows}"

        )

        errors.append({

            "type":
                "missing_data",

            "sheet":
                sheet_name,

            "expected_rows":
                expected_rows,

            "actual_rows":
                actual_rows,

            "missing_rows":
                missing_rows,

            # IMPORTANT:
            # Regardless of how many rows are missing,
            # this deficiency costs only one point.
            "weight":
                1

        })


    # ========================================================
    # CHECK 3 — REQUIRED COLUMNS
    # ========================================================
    #
    # IMPORTANT:
    #
    # This used to duplicate CHECK 1.
    #
    # Because required_columns are already part of the logical
    # column comparison, we do NOT create another check.
    #
    # This prevents:
    #
    # missing column
    #       +
    # required column
    #
    # from being counted twice.
    #
    # ========================================================

    required_columns = master_sheet.get(
        "required_columns",
        []
    )

    # Informational only.
    #
    # We do not create another deduction.
    missing_required = [

        required

        for required in required_columns

        if _find_matching_column(
            required,
            student_columns
        ) is None

    ]

    # No extra scoring/check counter here.


    # ========================================================
    # CHECK 4 — DATA TYPES
    # ========================================================

    total_checks += 1

    master_types = master_sheet.get(
        "data_types",
        {}
    )

    student_types = student_sheet.get(
        "data_types",
        {}
    )

    type_errors = 0

    normalized_student_types = {

        _normalize_text(key):
            value

        for key, value
        in student_types.items()

    }


    for master_column, expected_types in (
        master_types.items()
    ):

        normalized_column = _normalize_text(
            master_column
        )

        actual_types = (
            normalized_student_types.get(
                normalized_column
            )
        )

        if actual_types is None:

            continue


        expected_set = {

            _normalize_text(t)

            for t in expected_types

        }

        actual_set = {

            _normalize_text(t)

            for t in actual_types

        }


        if "any" in expected_set:

            continue


        numeric_expected = (

            "integer" in expected_set

            or

            "float" in expected_set

        )

        numeric_actual = (

            "integer" in actual_set

            or

            "float" in actual_set

        )


        if (
            numeric_expected
            and
            numeric_actual
        ):

            continue


        if expected_set.intersection(
            actual_set
        ):

            continue


        type_errors += 1

        feedback.append(

            f"[{sheet_name}] Wrong data type "
            f"for '{master_column}': "
            f"expected {expected_types}, "
            f"got {actual_types}"

        )

        errors.append({

            "type":
                "wrong_data_type",

            "sheet":
                sheet_name,

            "column":
                master_column,

            "expected":
                expected_types,

            "actual":
                actual_types

        })


    if type_errors == 0:

        checks_passed += 1


    # ========================================================
    # CHECK 5 — FORMULAS
    # ========================================================

    total_checks += 1

    master_formulas = master_sheet.get(
        "formulas",
        []
    )

    student_formulas = student_sheet.get(
        "formulas",
        []
    )


    if not master_formulas:

        checks_passed += 1

    else:

        used_student_indexes = set()

        missing_formula_requirements = []

        matched_formulas = []


        for master_formula in (
            master_formulas
        ):

            match_index = (
                _find_matching_student_formula(
                    master_formula,
                    student_formulas,
                    used_student_indexes
                )
            )

            if match_index is None:

                missing_formula_requirements.append(
                    master_formula
                )

            else:

                used_student_indexes.add(
                    match_index
                )

                matched_formulas.append(
                    (
                        master_formula,
                        student_formulas[
                            match_index
                        ]
                    )
                )


        if not missing_formula_requirements:

            checks_passed += 1

        else:

            for master_formula in (
                missing_formula_requirements
            ):

                formula_type = (
                    _get_formula_type(
                        master_formula
                    )
                )

                master_address = (
                    master_formula.get(
                        "cell_address"
                    )
                )

                master_header = (
                    master_formula.get(
                        "header"
                    )
                )

                feedback.append(

                    f"[{sheet_name}] Missing "
                    f"{formula_type} formula "
                    f"requirement"

                )

                error = {

                    "type":
                        "missing_formula",

                    "sheet":
                        sheet_name,

                    "cell":
                        master_address,

                    "header":
                        master_header,

                    "formula_type":
                        formula_type,

                    "expected":
                        master_formula.get(
                            "formula"
                        ),

                    "location_strict":
                        master_formula.get(
                            "location_strict",
                            False
                        )

                }

                formula_weight = (
                    master_formula.get(
                        "weight"
                    )
                )

                if formula_weight is not None:

                    error[
                        "weight"
                    ] = formula_weight

                errors.append(
                    error
                )


        # ----------------------------------------------------
        # Extra formulas are allowed.
        # ----------------------------------------------------

        if matched_formulas:

            for (
                master_formula,
                student_formula
            ) in matched_formulas:

                master_address = (
                    master_formula.get(
                        "cell_address"
                    )
                )

                student_address = (
                    student_formula.get(
                        "cell_address"
                    )
                )

                if (
                    master_address
                    !=
                    student_address
                ):

                    feedback.append(

                        f"[{sheet_name}] "
                        f"{_get_formula_type(master_formula)} "
                        f"formula accepted at "
                        f"{student_address} "
                        f"instead of "
                        f"{master_address}"

                    )


    # ========================================================
    # CHECK 6 — TABLES
    # ========================================================

    total_checks += 1

    master_tables = master_sheet.get(
        "tables",
        []
    )

    student_tables = student_sheet.get(
        "tables",
        []
    )


    if not master_tables:

        checks_passed += 1

    else:

        used_student_tables = set()

        missing_tables = []


        for master_table in (
            master_tables
        ):

            matched_index = None


            for index, student_table in enumerate(
                student_tables
            ):

                if index in used_student_tables:

                    continue


                if _table_structure_matches(
                    master_table,
                    student_table
                ):

                    matched_index = index

                    break


            if matched_index is None:

                missing_tables.append(
                    master_table
                )

                continue


            used_student_tables.add(
                matched_index
            )

            student_table = (
                student_tables[
                    matched_index
                ]
            )


            # ------------------------------------------------
            # OPTIONAL STRICT LOCATION
            # ------------------------------------------------

            if _table_location_is_strict(
                master_table
            ):

                master_range = (
                    master_table.get(
                        "range"
                    )
                )

                student_range = (
                    student_table.get(
                        "range"
                    )
                )


                master_start = (

                    master_range.split(
                        ":"
                    )[0].upper()

                    if master_range

                    else None

                )


                student_start = (

                    student_range.split(
                        ":"
                    )[0].upper()

                    if student_range

                    else None

                )


                if (
                    master_start
                    !=
                    student_start
                ):

                    errors.append({

                        "type":
                            "wrong_table",

                        "sheet":
                            sheet_name,

                        "table":
                            master_table.get(
                                "name"
                            ),

                        "problem":
                            "location",

                        "expected":
                            master_start,

                        "actual":
                            student_start,

                        "location_strict":
                            True,

                        "weight":
                            master_table.get(
                                "weight"
                            )

                    })


        # ----------------------------------------------------
        # Missing tables
        # ----------------------------------------------------

        if not missing_tables:

            table_errors = [

                error

                for error in errors

                if (

                    error.get(
                        "type"
                    )
                    ==
                    "wrong_table"

                    and

                    error.get(
                        "sheet"
                    )
                    ==
                    sheet_name

                )

            ]

            if not table_errors:

                checks_passed += 1

        else:

            for master_table in (
                missing_tables
            ):

                feedback.append(

                    f"[{sheet_name}] Missing table "
                    f"with required columns: "
                    f"{master_table.get('columns')}"

                )

                error = {

                    "type":
                        "missing_table",

                    "sheet":
                        sheet_name,

                    "table":
                        master_table.get(
                            "name"
                        ),

                    "expected_columns":
                        master_table.get(
                            "columns"
                        )

                }

                table_weight = (
                    master_table.get(
                        "weight"
                    )
                )

                if table_weight is not None:

                    error[
                        "weight"
                    ] = table_weight

                errors.append(
                    error
                )


    # ========================================================
    # CHECK 7 — DATA VALIDATION
    # ========================================================

    total_checks += 1

    master_dv = master_sheet.get(
        "data_validation",
        []
    )

    student_dv = student_sheet.get(
        "data_validation",
        []
    )


    if not master_dv:

        checks_passed += 1

    else:

        used = set()

        missing = []


        for master_rule in master_dv:

            matched = None


            for index, student_rule in enumerate(
                student_dv
            ):

                if index in used:

                    continue


                if _validation_matches(
                    master_rule,
                    student_rule
                ):

                    matched = index

                    break


            if matched is None:

                missing.append(
                    master_rule
                )

            else:

                used.add(
                    matched
                )


        if not missing:

            checks_passed += 1

        else:

            feedback.append(

                f"[{sheet_name}] Missing "
                f"{len(missing)} data validation rule(s)"

            )

            errors.append({

                "type":
                    "missing_data_validation",

                "sheet":
                    sheet_name,

                "expected_count":
                    len(master_dv),

                "actual_count":
                    len(student_dv)

            })


    # ========================================================
    # CHECK 8 — CONDITIONAL FORMATTING
    # ========================================================

    total_checks += 1

    master_cf = master_sheet.get(
        "conditional_formatting",
        []
    )

    student_cf = student_sheet.get(
        "conditional_formatting",
        []
    )


    if not master_cf:

        checks_passed += 1

    else:

        used = set()

        missing = []


        for master_rule in master_cf:

            matched = None


            for index, student_rule in enumerate(
                student_cf
            ):

                if index in used:

                    continue


                if _conditional_formatting_matches(
                    master_rule,
                    student_rule
                ):

                    matched = index

                    break


            if matched is None:

                missing.append(
                    master_rule
                )

            else:

                used.add(
                    matched
                )


        if not missing:

            checks_passed += 1

        else:

            feedback.append(

                f"[{sheet_name}] Missing "
                f"{len(missing)} conditional "
                f"formatting rule(s)"

            )

            errors.append({

                "type":
                    "missing_conditional_formatting",

                "sheet":
                    sheet_name,

                "expected_count":
                    len(master_cf),

                "actual_count":
                    len(student_cf)

            })


    # ========================================================
    # NO COLUMN WIDTH CHECK
    # ========================================================
    #
    # IMPORTANT:
    #
    # Column width is NOT a grading requirement.
    #
    # We intentionally do NOT:
    #
    #   - inspect column_widths
    #   - create wrong_column_width
    #   - add a check
    #   - add feedback
    #
    # Therefore column width has ZERO effect on:
    #
    #   score
    #   accuracy
    #   checks
    #   feedback
    #
    # ========================================================


    # ========================================================
    # CHECK 9 — MERGED CELLS
    # ========================================================

    total_checks += 1

    master_merged = master_sheet.get(
        "merged_cells",
        []
    )

    student_merged = student_sheet.get(
        "merged_cells",
        []
    )


    if not master_merged:

        checks_passed += 1

    else:

        if _merged_cells_match(
            master_sheet,
            student_sheet
        ):

            checks_passed += 1

        else:

            feedback.append(

                f"[{sheet_name}] Merged cell "
                f"structure mismatch"

            )

            errors.append({

                "type":
                    "missing_merged_cell",

                "sheet":
                    sheet_name,

                "expected":
                    master_merged,

                "actual":
                    student_merged

            })


    # ========================================================
    # RESULT
    # ========================================================

    return {

        "feedback":
            feedback,

        "errors":
            errors,

        "checks_passed":
            checks_passed,

        "total_checks":
            total_checks

    }


# ============================================================
# EMPTY PROJECT
# ============================================================

def is_empty_project(
    student_rules
):

    if student_rules.get(
        "total_sheets",
        0
    ) == 0:

        return True


    sheets = student_rules.get(
        "sheets",
        {}
    )


    if not sheets:

        return True


    for sheet_name, sheet in (
        sheets.items()
    ):

        if sheet.get(
            "total_columns",
            0
        ) > 0:

            return False


        if sheet.get(
            "data_rows",
            0
        ) > 0:

            return False


        if sheet.get(
            "formulas"
        ):

            return False


        if sheet.get(
            "tables"
        ):

            return False


        if sheet.get(
            "data_validation"
        ):

            return False


        if sheet.get(
            "conditional_formatting"
        ):

            return False


        if sheet.get(
            "merged_cells"
        ):

            return False


    return True


# ============================================================
# COMPLETE STRUCTURE COMPARISON
# ============================================================

def compare_structure(
    student_rules,
    master_rules
):

    # ========================================================
    # EMPTY PROJECT
    # ========================================================

    if is_empty_project(
        student_rules
    ):

        empty_errors = [

            {
                "type":
                    "empty_project"
            }

        ]


        score_details = get_score_details(
            empty_errors,
            starting_score=MAX_SCORE
        )


        student_feedback = generate_feedback(
            empty_errors
        )


        return {

            "score":
                score_details[
                    "final_score"
                ],

            "max_score":
                MAX_SCORE,

            "status":
                score_details[
                    "status"
                ],

            "score_details":
                score_details,

            "student_feedback":
                student_feedback,

            "feedback": [

                "The submitted project is empty."

            ],

            "errors":
                empty_errors,

            "passed":
                False,

            "total_checks":
                0,

            "checks_passed":
                0,

            "summary":
                (
                    f"Score: "
                    f"{score_details['final_score']}/"
                    f"{MAX_SCORE} | "
                    f"Empty Project"
                )

        }


    # ========================================================
    # TRACKING
    # ========================================================

    all_feedback = []

    all_errors = []

    total_checks = 0

    total_passed = 0


    # ========================================================
    # SHEET COUNT
    # ========================================================

    total_checks += 1

    expected_sheets = master_rules.get(
        "total_sheets",
        0
    )

    actual_sheets = student_rules.get(
        "total_sheets",
        0
    )


    if actual_sheets == expected_sheets:

        total_passed += 1

    else:

        difference = abs(
            actual_sheets
            -
            expected_sheets
        )

        all_feedback.append(

            f"Sheet count mismatch: "
            f"expected {expected_sheets}, "
            f"got {actual_sheets}"

        )

        all_errors.append({

            "type":
                "sheet_count_mismatch",

            "expected":
                expected_sheets,

            "actual":
                actual_sheets,

            "difference":
                difference

        })


    # ========================================================
    # SHEET NAMES
    # ========================================================

    total_checks += 1

    master_sheet_names = {

        _normalize_text(name):
            name

        for name
        in master_rules.get(
            "sheet_names",
            []
        )

    }

    student_sheet_names = {

        _normalize_text(name):
            name

        for name
        in student_rules.get(
            "sheet_names",
            []
        )

    }


    missing_sheet_keys = (

        set(master_sheet_names)

        -
        
        set(student_sheet_names)

    )


    extra_sheet_keys = (

        set(student_sheet_names)

        -

        set(master_sheet_names)

    )


    if not missing_sheet_keys:

        total_passed += 1

    else:

        missing_names = [

            master_sheet_names[key]

            for key in missing_sheet_keys

        ]


        all_feedback.append(

            f"Missing sheets: "
            f"{', '.join(missing_names)}"

        )


        for sheet_name in missing_names:

            all_errors.append({

                "type":
                    "missing_sheet",

                "sheet":
                    sheet_name

            })


    if extra_sheet_keys:

        extra_names = [

            student_sheet_names[key]

            for key in extra_sheet_keys

        ]


        all_feedback.append(

            f"Extra sheets: "
            f"{', '.join(extra_names)}"

        )


        for sheet_name in extra_names:

            all_errors.append({

                "type":
                    "extra_sheet",

                "sheet":
                    sheet_name

            })


    # ========================================================
    # PER SHEET
    # ========================================================

    master_sheets_data = master_rules.get(
        "sheets",
        {}
    )

    student_sheets_data = student_rules.get(
        "sheets",
        {}
    )


    normalized_student_sheets = {

        _normalize_text(name):
            sheet

        for name, sheet
        in student_sheets_data.items()

    }


    for master_sheet_name in (
        master_rules.get(
            "sheet_names",
            []
        )
    ):

        normalized_name = _normalize_text(
            master_sheet_name
        )


        student_sheet_name = (
            normalized_student_sheets.get(
                normalized_name
            )
        )


        if student_sheet_name is None:

            continue


        master_sheet = (
            master_sheets_data.get(
                master_sheet_name,
                {}
            )
        )


        result = compare_sheets(

            student_sheet_name,

            master_sheet,

            master_sheet_name

        )


        all_feedback.extend(
            result["feedback"]
        )


        all_errors.extend(
            result["errors"]
        )


        total_checks += (
            result["total_checks"]
        )


        total_passed += (
            result["checks_passed"]
        )


    # ========================================================
    # SCORING
    # ========================================================

    score_details = get_score_details(

        all_errors,

        starting_score=MAX_SCORE

    )


    final_score = (
        score_details[
            "final_score"
        ]
    )


    # ========================================================
    # PASS / FAIL
    # ========================================================

    critical_error = any(

        error.get("type")

        in {

            "missing_sheet",

            "sheet_count_mismatch"

        }

        for error in all_errors

    )


    if critical_error:

        passed = False

    else:

        passed = (

            final_score
            >=
            PASSING_SCORE

        )


    # ========================================================
    # FEEDBACK
    # ========================================================

    student_feedback = generate_feedback(
        all_errors
    )


    ai_feedback = None


    if all_errors:

        ai_result = (
            generate_ai_enhanced_feedback(

                all_errors,

                score_details

            )
        )


        if isinstance(
            ai_result,
            dict
        ):

            ai_feedback = ai_result.get(
                "ai_feedback"
            )

        elif isinstance(
            ai_result,
            str
        ):

            ai_feedback = ai_result


    # ========================================================
    # RESULT
    # ========================================================

    return {

        "score":
            final_score,

        "max_score":
            MAX_SCORE,

        "status":
            score_details[
                "status"
            ],

        "score_details":
            score_details,

        "student_feedback":
            student_feedback,

        "ai_feedback":
            ai_feedback,

        "feedback":
            all_feedback,

        "errors":
            all_errors,

        "passed":
            passed,

        "total_checks":
            total_checks,

        "checks_passed":
            total_passed,

        "summary":
            (

                f"Score: "
                f"{final_score}/"
                f"{MAX_SCORE} | "

                f"Checks: "
                f"{total_passed}/"
                f"{total_checks} | "

                f"Deduction: "
                f"{score_details['total_deduction']}"

            )

    }


# ============================================================
# REPORT
# ============================================================

def generate_report(
    result,
    student_name,
    project_id
):

    total_checks = result[
        "total_checks"
    ]

    checks_passed = result[
        "checks_passed"
    ]


    accuracy = round(

        (

            checks_passed

            /

            max(
                1,
                total_checks
            )

        )

        *

        100,

        1

    )


    score_details = result.get(
        "score_details",
        {}
    )


    return {

        "student":
            student_name,

        "project":
            project_id,

        "score":
            result["score"],

        "max_score":
            MAX_SCORE,

        "status":

            (
                "PASSED"

                if result["passed"]

                else

                "FAILED"
            ),

        "score_status":

            result.get(

                "status",

                get_score_status(
                    result["score"]
                )

            ),

        "score_breakdown":
            score_details,

        "feedback":
            result["feedback"],

        "errors":
            result.get(
                "errors",
                []
            ),

        "student_feedback":
            result.get(
                "student_feedback",
                []
            ),

        "ai_feedback":
            result.get(
                "ai_feedback"
            ),

        "summary":
            result["summary"],

        "details": {

            "total_checks":
                total_checks,

            "checks_passed":
                checks_passed,

            "accuracy":
                accuracy,

            "starting_score":
                MAX_SCORE,

            "total_deduction":

                score_details.get(

                    "total_deduction",

                    MAX_SCORE
                    -
                    result["score"]

                ),

            "final_score":
                result["score"],

            "max_score":
                MAX_SCORE

        }

    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    from analyzer.excel_analyzer import (
        extract_full_rules
    )


    print("=" * 70)

    print(
        "FLEXIBLE AUTO GRADER TEST"
    )

    print("=" * 70)


    # --------------------------------------------------------
    # MASTER
    # --------------------------------------------------------

    master_file = (
        "student_project2.xlsx"
    )

    student_file = (
        "student_project3.xlsx"
    )

    project_id = (
        "Project_1"
    )


    print(
        "\n=== MASTER ==="
    )


    master_rules = extract_full_rules(
        master_file
    )


    save_master_rules(
        master_rules,
        project_id
    )


    # --------------------------------------------------------
    # LOAD MASTER
    # --------------------------------------------------------

    master = load_master_rules(
        project_id
    )


    # --------------------------------------------------------
    # STUDENT
    # --------------------------------------------------------

    print(
        "\n=== STUDENT ==="
    )


    student_rules = extract_full_rules(
        student_file
    )


    # --------------------------------------------------------
    # COMPARE
    # --------------------------------------------------------

    result = compare_structure(

        student_rules,

        master

    )


    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    report = generate_report(

        result,

        "Test Student",

        project_id

    )


    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    print(
        "\n"
        +
        "=" * 70
    )


    print(

        f"SCORE: "
        f"{result['score']}/"
        f"{MAX_SCORE}"

    )


    print(

        f"STATUS: "
        f"{'✅ PASSED' if result['passed'] else '❌ FAILED'}"

    )


    print(

        f"CHECKS: "
        f"{result['checks_passed']}/"
        f"{result['total_checks']}"

    )


    print(

        f"ACCURACY: "
        f"{report['details']['accuracy']}%"

    )


    print("=" * 70)


    # --------------------------------------------------------
    # SCORE BREAKDOWN
    # --------------------------------------------------------

    details = result.get(
        "score_details",
        {}
    )


    print(
        "\nSCORE BREAKDOWN:"
    )

    print(
        "-" * 70
    )


    print(

        f"Starting Score: "
        f"{details.get('starting_score', MAX_SCORE)}/"
        f"{MAX_SCORE}"

    )


    print(
        "\nDeductions:"
    )


    for item in details.get(
        "error_deductions",
        []
    ):

        ignored_text = ""

        if item.get(
            "ignored",
            False
        ):

            ignored_text = (
                " [IGNORED]"
            )


        print(

            f"  {item['number']}. "
            f"{item['type']} "
            f"({item['category']}): "
            f"-{item['deduction']}"
            f"{ignored_text}"

        )


    print(

        f"\nTotal Deduction: "
        f"-{details.get('total_deduction', 0)}"

    )


    print(

        f"Final Score: "
        f"{details.get('final_score', result['score'])}/"
        f"{MAX_SCORE}"

    )


    print(

        f"Status: "
        f"{details.get('status', result['status'])}"

    )


    # --------------------------------------------------------
    # FEEDBACK
    # --------------------------------------------------------

    if result["feedback"]:

        print(
            "\nFEEDBACK:"
        )


        for feedback in result[
            "feedback"
        ]:

            print(
                f"  • {feedback}"
            )

    else:

        print(
            "\n✅ Perfect! No issues found."
        )


    # --------------------------------------------------------
    # ERRORS
    # --------------------------------------------------------

    if result["errors"]:

        print(
            "\nDETECTED ERRORS:"
        )


        for error in result[
            "errors"
        ]:

            print(
                f"  • {error}"
            )


    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print(

        f"\n{result['summary']}"

    )


    # --------------------------------------------------------
    # STUDENT FEEDBACK
    # --------------------------------------------------------

    if result.get(
        "student_feedback"
    ):

        print(
            "\nSTUDENT FEEDBACK:"
        )


        for item in result[
            "student_feedback"
        ]:

            print(

                f"\n[{item['severity'].upper()}] "
                f"{item['title']}"

            )


            print(

                f"  {item['message']}"

            )


    # --------------------------------------------------------
    # AI FEEDBACK
    # --------------------------------------------------------

    ai_feedback = result.get(
        "ai_feedback"
    )


    if ai_feedback:

        print(
            "\nAI STUDENT EXPLANATION:"
        )

        print(
            "-" * 70
        )

        print(
            ai_feedback
        )

        print(
            "-" * 70
        )


    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    report_path = save_report_json(

        report,

        "Test Student",

        project_id

    )


    print(

        f"\n✅ Complete report saved to: "
        f"{report_path}"

    )