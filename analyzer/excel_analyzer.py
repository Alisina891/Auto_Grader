import os
import re
from datetime import datetime, date, time

import openpyxl
from openpyxl.utils import get_column_letter


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(value):
    """
    Normalize text for flexible comparison.

    Differences such as:
        "Name"
        " name "
        "NAME"

    are treated as the same.
    """

    if value is None:
        return ""

    text = str(value)

    # Normalize whitespace
    text = " ".join(text.strip().split())

    # Normalize common invisible characters
    text = (
        text
        .replace("\u200c", "")
        .replace("\u200f", "")
        .replace("\ufeff", "")
    )

    return text.casefold()


def normalize_formula_text(formula):
    """
    Normalize formula text without changing its logic.
    """

    if formula is None:
        return ""

    formula = str(formula).strip()

    formula = formula.replace(" ", "")

    return formula.casefold()


# ============================================================
# WORKBOOK INFO
# ============================================================

def get_workbook_info(filepath):
    """Return basic workbook information."""

    wb = openpyxl.load_workbook(
        filepath,
        data_only=False
    )

    info = {
        "file_name": os.path.basename(filepath),
        "sheet_names": wb.sheetnames,
        "total_sheets": len(wb.sheetnames)
    }

    wb.close()

    return info


# ============================================================
# DATA START
# ============================================================

def find_data_start(sheet):
    """
    Find the first meaningful row.

    The first row containing at least one non-empty cell
    within the first 20 rows is considered the header/data
    starting row.
    """

    max_scan_row = min(
        20,
        sheet.max_row
    )

    for row in range(1, max_scan_row + 1):

        for col in range(
            1,
            sheet.max_column + 1
        ):

            value = sheet.cell(
                row=row,
                column=col
            ).value

            if value is not None and str(value).strip():

                return row

    return 1


# ============================================================
# CELL FORMAT
# ============================================================

def extract_cell_format(cell):
    """Extract useful formatting information."""

    font_color = None

    try:
        if (
            cell.font
            and cell.font.color
            and cell.font.color.type == "rgb"
        ):
            font_color = cell.font.color.rgb
    except Exception:
        font_color = None

    fill_color = None

    try:
        if (
            cell.fill
            and cell.fill.fgColor
            and cell.fill.fgColor.type == "rgb"
        ):
            fill_color = cell.fill.fgColor.rgb
    except Exception:
        fill_color = None

    return {

        "font": {
            "name": cell.font.name,
            "size": cell.font.size,
            "bold": cell.font.bold,
            "italic": cell.font.italic,
            "color": str(font_color)
            if font_color
            else None
        },

        "fill": {
            "color": str(fill_color)
            if fill_color
            else None,
            "pattern": cell.fill.patternType
        },

        "border": {
            "left": cell.border.left.style,
            "right": cell.border.right.style,
            "top": cell.border.top.style,
            "bottom": cell.border.bottom.style
        },

        "alignment": {
            "horizontal": cell.alignment.horizontal,
            "vertical": cell.alignment.vertical,
            "wrap_text": cell.alignment.wrapText
        },

        "number_format": (
            cell.number_format
            if cell.number_format
            else "General"
        )
    }


# ============================================================
# DATA TYPE
# ============================================================

def detect_data_type(value):

    if value is None:
        return None

    if isinstance(value, bool):
        return "boolean"

    if isinstance(value, datetime):
        return "date"

    if isinstance(value, date):
        return "date"

    if isinstance(value, time):
        return "time"

    if isinstance(value, int):
        return "integer"

    if isinstance(value, float):
        return "float"

    if isinstance(value, str):

        if value.startswith("="):
            return "formula"

        return "string"

    return type(value).__name__


# ============================================================
# HEADERS
# ============================================================

def extract_headers(sheet, header_row):
    """
    Extract headers together with their physical positions.

    IMPORTANT:
    Position is stored as INFORMATION only.

    It is NOT the identity of a column.
    """

    headers = []

    for col in range(
        1,
        sheet.max_column + 1
    ):

        value = sheet.cell(
            row=header_row,
            column=col
        ).value

        headers.append(value)

    return headers


def extract_column_metadata(sheet, header_row):
    """
    Extract column information.

    Columns are identified primarily by HEADER,
    not Excel column letter.
    """

    columns = []

    for col in range(
        1,
        sheet.max_column + 1
    ):

        cell = sheet.cell(
            row=header_row,
            column=col
        )

        header = cell.value

        if header is None:
            continue

        header_text = str(header).strip()

        if not header_text:
            continue

        columns.append({

            "header": header_text,

            "normalized_header":
                normalize_text(header_text),

            "column_number": col,

            "column_letter":
                get_column_letter(col),

            "position": col
        })

    return columns


# ============================================================
# DATA TYPES
# ============================================================

def extract_data_types(
    sheet,
    header_row,
    column_metadata
):
    """
    Detect data types by HEADER.

    Physical column position is not used as the identity.
    """

    data_types = {}

    max_sample_rows = min(
        sheet.max_row,
        header_row + 5
    )

    for column in column_metadata:

        header = column["header"]
        col_number = column["column_number"]

        types_found = set()

        for row in range(
            header_row + 1,
            max_sample_rows + 1
        ):

            value = sheet.cell(
                row=row,
                column=col_number
            ).value

            detected = detect_data_type(value)

            if detected:
                types_found.add(detected)

        data_types[header] = (
            sorted(types_found)
            if types_found
            else ["any"]
        )

    return data_types


# ============================================================
# FORMULA FUNCTIONS
# ============================================================

KNOWN_FORMULA_TYPES = (
    "SUM",
    "AVERAGE",
    "COUNT",
    "COUNTA",
    "MAX",
    "MIN",
    "IF",
    "VLOOKUP",
    "HLOOKUP",
    "SUMIF",
    "SUMIFS",
    "COUNTIF",
    "COUNTIFS",
    "AVERAGEIF",
    "AVERAGEIFS",
    "ROUND",
    "RANK",
    "INDEX",
    "MATCH",
    "AND",
    "OR",
    "NOT",
)


def extract_formula_functions(formula):
    """
    Extract ALL Excel functions from a formula.

    Example:

        =IF(AVERAGE(B2:B10)>50,SUM(B2:B10),0)

    returns:

        ["IF", "AVERAGE", "SUM"]
    """

    if not formula:
        return []

    text = str(formula).upper()

    functions = []

    for function_name in KNOWN_FORMULA_TYPES:

        pattern = rf"\b{re.escape(function_name)}\s*\("

        if re.search(pattern, text):

            functions.append(function_name)

    return functions


def extract_formula_type(formula):
    """
    Return the primary formula type.

    The first recognized function is used as the main type.
    """

    functions = extract_formula_functions(formula)

    if functions:
        return functions[0]

    return "OTHER"


# ============================================================
# FORMULA EXTRACTION
# ============================================================

def extract_formulas(
    sheet,
    header_row,
    column_metadata
):
    """
    Extract formulas from the workbook.

    Formula location is stored for information only.

    Matching should NOT depend on the location.
    """

    formulas = []

    formula_map = {}

    for row in range(
        header_row + 1,
        sheet.max_row + 1
    ):

        for column in column_metadata:

            col_number = column["column_number"]

            cell = sheet.cell(
                row=row,
                column=col_number
            )

            value = cell.value

            if not (
                isinstance(value, str)
                and value.startswith("=")
            ):
                continue

            header = column["header"]

            formula_type = extract_formula_type(
                value
            )

            formula_functions = (
                extract_formula_functions(value)
            )

            formula_info = {

                # ------------------------------------------------
                # Physical position
                # ------------------------------------------------
                "row": row,

                "column": col_number,

                "column_letter":
                    get_column_letter(col_number),

                "cell_address":
                    cell.coordinate,

                # ------------------------------------------------
                # Logical identity
                # ------------------------------------------------
                "header": header,

                "normalized_header":
                    normalize_text(header),

                # ------------------------------------------------
                # Formula
                # ------------------------------------------------
                "formula": value,

                "normalized_formula":
                    normalize_formula_text(value),

                "formula_type":
                    formula_type,

                "formula_functions":
                    formula_functions,

                # ------------------------------------------------
                # Location is NOT strict by default
                # ------------------------------------------------
                "location_strict": False
            }

            formulas.append(
                formula_info
            )

            header_key = str(header)

            if header_key not in formula_map:

                formula_map[header_key] = []

            formula_map[header_key].append(
                formula_info
            )

    return formulas, formula_map


# ============================================================
# FORMATTING
# ============================================================

def extract_formatting(
    sheet,
    header_row,
    column_metadata
):
    """
    Extract formatting by HEADER.

    This prevents column movement from creating
    false formatting errors.
    """

    formatting = {}

    for column in column_metadata:

        header = column["header"]

        col_number = column["column_number"]

        header_cell = sheet.cell(
            row=header_row,
            column=col_number
        )

        formatting[header] = {

            "normalized_header":
                normalize_text(header),

            "column_letter":
                get_column_letter(col_number),

            "header_format":
                extract_cell_format(header_cell),

            "data_formats": []
        }

        max_sample_row = min(
            sheet.max_row,
            header_row + 4
        )

        for row in range(
            header_row + 1,
            max_sample_row + 1
        ):

            cell = sheet.cell(
                row=row,
                column=col_number
            )

            fmt = extract_cell_format(
                cell
            )

            if (
                fmt
                not in formatting[header]["data_formats"]
            ):

                formatting[header]["data_formats"].append(
                    fmt
                )

    return formatting


# ============================================================
# COLUMN WIDTHS
# ============================================================

def extract_column_widths(
    sheet,
    header_row,
    column_metadata
):
    """
    Store column widths by HEADER.

    This is critical.

    Old system:
        "F": 15

    New system:
        "Average": 15

    Therefore moving Average from F -> G
    does not create a false error.
    """

    widths = {}

    for column in column_metadata:

        header = column["header"]

        col_letter = column["column_letter"]

        width = sheet.column_dimensions[
            col_letter
        ].width

        if width is None:
            width = 8.43

        widths[header] = {

            "normalized_header":
                normalize_text(header),

            "width": float(width)
        }

    return widths


# ============================================================
# TABLES
# ============================================================

def extract_tables(sheet):

    tables = []

    for table_name in sheet.tables:

        table = sheet.tables[
            table_name
        ]

        columns = []

        for col in table.tableColumns:

            columns.append(
                str(col.name)
            )

        tables.append({

            "name": table_name,

            # Physical range is informational.
            "range": table.ref,

            "start_cell":
                table.ref.split(":", 1)[0]
                if table.ref
                else None,

            "columns": columns,

            "normalized_columns": [
                normalize_text(col)
                for col in columns
            ],

            "style":
                (
                    table.tableStyleInfo.name
                    if table.tableStyleInfo
                    else None
                ),

            "show_header":
                (
                    table.headerRowCount == 1
                    if hasattr(
                        table,
                        "headerRowCount"
                    )
                    else True
                ),

            "show_totals":
                (
                    table.totalsRowCount == 1
                    if hasattr(
                        table,
                        "totalsRowCount"
                    )
                    else False
                ),

            # Flexible by default
            "location_strict": False,

            "name_strict": False
        })

    return tables


# ============================================================
# DATA VALIDATION
# ============================================================

def extract_data_validation(sheet):

    validations = []

    for dv in sheet.data_validations.dataValidation:

        rule = {

            "type": dv.type,

            "operator": dv.operator,

            "formula1": dv.formula1,

            "formula2": dv.formula2,

            "allow_blank": dv.allow_blank,

            "show_error":
                dv.showErrorMessage,

            "error_message":
                dv.error,

            "prompt_message":
                dv.prompt,

            # Physical range is informational
            "range":
                str(dv.sqref)
                if dv.sqref
                else None,

            # Flexible by default
            "location_strict": False
        }

        validations.append(rule)

    return validations


# ============================================================
# CONDITIONAL FORMATTING
# ============================================================

def extract_conditional_formatting(sheet):

    rules = []

    for cf in sheet.conditional_formatting:

        for rule in cf.rules:

            formula = getattr(
                rule,
                "formula",
                None
            )

            if formula is not None:
                formula = list(formula)

            rules.append({

                # Physical range is informational
                "range":
                    str(cf),

                "type":
                    rule.type,

                "operator":
                    getattr(
                        rule,
                        "operator",
                        None
                    ),

                "formula":
                    formula,

                "priority":
                    getattr(
                        rule,
                        "priority",
                        None
                    ),

                "location_strict":
                    False
            })

    return rules


# ============================================================
# MERGED CELLS
# ============================================================

def extract_merged_cells(sheet):

    return [
        str(mc)
        for mc in sheet.merged_cells.ranges
    ]


# ============================================================
# MERGED CELL SHAPES
# ============================================================

def merged_cell_shape(range_string):

    """
    Convert:

        B2:F5

    into:

        rows = 4
        columns = 5

    This allows merged areas to move.

    """

    if not range_string:
        return None

    try:

        start, end = range_string.split(":")

        start_cell = openpyxl.utils.cell.coordinate_to_tuple(
            start
        )

        end_cell = openpyxl.utils.cell.coordinate_to_tuple(
            end
        )

        start_row, start_col = start_cell
        end_row, end_col = end_cell

        return {
            "rows":
                end_row - start_row + 1,

            "columns":
                end_col - start_col + 1
        }

    except Exception:

        return None


def extract_merged_cell_shapes(sheet):

    shapes = []

    for merged in extract_merged_cells(sheet):

        shape = merged_cell_shape(
            merged
        )

        if shape:

            shapes.append(shape)

    return shapes


# ============================================================
# MAIN RULE EXTRACTION
# ============================================================

def extract_full_rules(filepath):
    """
    Extract flexible, position-independent rules from
    ANY Excel workbook.

    IMPORTANT DESIGN PRINCIPLE:

        Cell address = information

        Header / formula type / table structure
        = logical requirement
    """

    wb = openpyxl.load_workbook(
        filepath,
        data_only=False
    )

    rules = {

        "file_name":
            os.path.basename(filepath),

        "total_sheets":
            len(wb.sheetnames),

        "sheet_names":
            wb.sheetnames,

        "sheets": {}
    }

    for sheet_name in wb.sheetnames:

        sheet = wb[sheet_name]

        header_row = find_data_start(
            sheet
        )

        # ----------------------------------------------------
        # Columns
        # ----------------------------------------------------

        headers = extract_headers(
            sheet,
            header_row
        )

        column_metadata = (
            extract_column_metadata(
                sheet,
                header_row
            )
        )

        # ----------------------------------------------------
        # Data types
        # ----------------------------------------------------

        data_types = extract_data_types(
            sheet,
            header_row,
            column_metadata
        )

        # ----------------------------------------------------
        # Formulas
        # ----------------------------------------------------

        formulas, formula_map = (
            extract_formulas(
                sheet,
                header_row,
                column_metadata
            )
        )

        # ----------------------------------------------------
        # Formatting
        # ----------------------------------------------------

        formatting = extract_formatting(
            sheet,
            header_row,
            column_metadata
        )

        # ----------------------------------------------------
        # Widths
        # ----------------------------------------------------

        column_widths = extract_column_widths(
            sheet,
            header_row,
            column_metadata
        )

        # ----------------------------------------------------
        # Tables
        # ----------------------------------------------------

        tables = extract_tables(
            sheet
        )

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        validations = extract_data_validation(
            sheet
        )

        # ----------------------------------------------------
        # Conditional Formatting
        # ----------------------------------------------------

        conditional_formatting = (
            extract_conditional_formatting(
                sheet
            )
        )

        # ----------------------------------------------------
        # Merged cells
        # ----------------------------------------------------

        merged_cells = extract_merged_cells(
            sheet
        )

        merged_shapes = (
            extract_merged_cell_shapes(
                sheet
            )
        )

        # ----------------------------------------------------
        # Data rows
        # ----------------------------------------------------

        data_rows = max(
            0,
            sheet.max_row - header_row
        )

        # ----------------------------------------------------
        # Logical columns
        # ----------------------------------------------------

        logical_columns = [
            col["header"]
            for col in column_metadata
        ]

        normalized_columns = [
            col["normalized_header"]
            for col in column_metadata
        ]

        # ----------------------------------------------------
        # Sheet rules
        # ----------------------------------------------------

        rules["sheets"][sheet_name] = {

            # ------------------------------------------------
            # Basic
            # ------------------------------------------------

            "header_row":
                header_row,

            "total_rows":
                sheet.max_row,

            "data_rows":
                data_rows,

            "total_columns":
                len(logical_columns),

            # ------------------------------------------------
            # Logical columns
            # ------------------------------------------------

            "columns":
                logical_columns,

            "normalized_columns":
                normalized_columns,

            "column_metadata":
                column_metadata,

            "required_columns":
                logical_columns,

            # ------------------------------------------------
            # Data types
            # ------------------------------------------------

            "data_types":
                data_types,

            # ------------------------------------------------
            # Formulas
            # ------------------------------------------------

            "has_formulas":
                len(formulas) > 0,

            "formula_count":
                len(formulas),

            "formulas":
                formulas,

            "formula_map":
                formula_map,

            # ------------------------------------------------
            # Formatting
            # ------------------------------------------------

            "formatting":
                formatting,

            "column_widths":
                column_widths,

            # ------------------------------------------------
            # Tables
            # ------------------------------------------------

            "tables":
                tables,

            # ------------------------------------------------
            # Validation
            # ------------------------------------------------

            "data_validation":
                validations,

            # ------------------------------------------------
            # Conditional formatting
            # ------------------------------------------------

            "conditional_formatting":
                conditional_formatting,

            # ------------------------------------------------
            # Merged cells
            # ------------------------------------------------

            "merged_cells":
                merged_cells,

            "merged_cell_shapes":
                merged_shapes
        }

    wb.close()

    return rules


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    filepath = "student_project.xlsx"

    print("=" * 70)
    print("FLEXIBLE EXCEL ANALYZER")
    print("=" * 70)

    rules = extract_full_rules(
        filepath
    )

    print(
        f"\nFile: {rules['file_name']}"
    )

    print(
        f"Sheets: {rules['total_sheets']}"
    )

    print(
        f"Sheet Names: {rules['sheet_names']}"
    )

    for sheet_name, sheet_rules in (
        rules["sheets"].items()
    ):

        print("\n" + "=" * 70)

        print(
            f"SHEET: {sheet_name}"
        )

        print("=" * 70)

        print(
            f"Header Row: "
            f"{sheet_rules['header_row']}"
        )

        print(
            f"Data Rows: "
            f"{sheet_rules['data_rows']}"
        )

        print(
            f"Logical Columns: "
            f"{sheet_rules['total_columns']}"
        )

        print("\nColumns:")

        for column in sheet_rules[
            "column_metadata"
        ]:

            print(
                f"  - {column['header']} "
                f"({column['column_letter']})"
            )

        print("\nFormulas:")

        for formula in sheet_rules[
            "formulas"
        ]:

            print(
                f"  - "
                f"{formula['cell_address']} | "
                f"{formula['header']} | "
                f"{formula['formula_type']} | "
                f"{formula['formula']}"
            )

        print("\nTables:")

        for table in sheet_rules[
            "tables"
        ]:

            print(
                f"  - {table['name']} | "
                f"{table['range']} | "
                f"{table['columns']}"
            )

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)