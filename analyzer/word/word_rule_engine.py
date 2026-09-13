# analyzer/word/word_rule_engine.py

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from analyzer.word.word_analyzer import extract_full_rules


# ============================================================
# CONFIGURATION
# ============================================================

PASSING_SCORE = 12

BASE_DIR = Path(__file__).resolve().parent.parent.parent

WORD_MASTER_RULES_DIR = BASE_DIR / "master_rules" / "word"
WORD_MASTER_FILE_NAME = "master_word.json"


# ============================================================
# PROJECT ID / FILE PATH HELPERS
# ============================================================

def _normalize_project_id(project_id: Any) -> str:
    """
    Convert project ID into a safe folder name.

    Examples:
        1       -> project_1
        "1"     -> project_1
        "project_1" -> project_1
    """

    value = str(project_id).strip()

    if not value:
        raise ValueError("project_id is required")

    # Prevent path traversal
    value = value.replace("\\", "_")
    value = value.replace("/", "_")

    # Keep only safe characters
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", value)

    if value.lower().startswith("project_"):
        suffix = value[len("project_"):]

        if not suffix:
            raise ValueError("Invalid project_id")

        return f"project_{suffix}"

    return f"project_{value}"


def _get_word_master_path(project_id: Any) -> Path:
    """
    Return the local path of the Word master rules file.
    """

    normalized_project_id = _normalize_project_id(project_id)

    project_dir = WORD_MASTER_RULES_DIR / normalized_project_id

    project_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return project_dir / WORD_MASTER_FILE_NAME


# ============================================================
# MASTER RULE STORAGE
# ============================================================

def save_master_rules(
    rules: Dict[str, Any],
    project_id: Any
) -> str:
    """
    Save Word master rules locally.

    Example:

        master_rules/
        └── word/
            └── project_1/
                └── master_word.json

    If the same project already has a master JSON,
    the old JSON is replaced.
    """

    if not isinstance(rules, dict):
        raise ValueError(
            "Word master rules must be a dictionary."
        )

    path = _get_word_master_path(project_id)

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Remove old JSON files from the same project folder
    # --------------------------------------------------------

    for old_file in path.parent.glob("*.json"):

        try:
            old_file.unlink()

        except OSError as error:

            print(
                f"⚠️ Could not delete old Word master rule file: "
                f"{old_file} | {error}"
            )

    # --------------------------------------------------------
    # Save new master rules
    # --------------------------------------------------------

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            rules,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"✅ Word master rules saved: {path}"
    )

    return str(path)


def load_master_rules(
    project_id: Any
) -> Optional[Dict[str, Any]]:
    """
    Load Word master rules from local storage.
    """

    path = _get_word_master_path(project_id)

    if not path.exists():

        print(
            f"⚠️ No Word master rules found for "
            f"Project {project_id}: {path}"
        )

        return None

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            rules = json.load(file)

    except json.JSONDecodeError as error:

        print(
            f"❌ Invalid Word master rules JSON: "
            f"{path} | {error}"
        )

        return None

    except OSError as error:

        print(
            f"❌ Could not read Word master rules: "
            f"{path} | {error}"
        )

        return None

    if not isinstance(rules, dict):

        print(
            f"❌ Word master rules are not a dictionary: "
            f"{path}"
        )

        return None

    print(
        f"✅ Word master rules loaded: {path}"
    )

    return rules


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def normalize_text(value: Any) -> str:
    """
    Normalize text for comparison.

    Differences such as:
    - uppercase/lowercase
    - multiple spaces
    - leading/trailing spaces
    - zero-width characters

    will not normally affect comparison.
    """

    if value is None:
        return ""

    text = str(value)

    # Remove zero-width characters
    text = re.sub(
        r"[\u200b\u200c\u200d\ufeff]",
        "",
        text
    )

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip().lower()


def _safe_int(value: Any, default: int = 0) -> int:

    try:
        return int(value)

    except (TypeError, ValueError):
        return default


def _safe_list(value: Any) -> List[Any]:

    if isinstance(value, list):
        return value

    return []


# ============================================================
# ERROR CREATION
# ============================================================

def create_error(
    category: str,
    message: str,
    expected: Any = None,
    actual: Any = None,
    weight: int = 1
) -> Dict[str, Any]:

    error = {
        "category": category,
        "message": message,
        "weight": weight,
    }

    if expected is not None:
        error["expected"] = expected

    if actual is not None:
        error["actual"] = actual

    return error


# ============================================================
# EMPTY DOCUMENT
# ============================================================

def is_empty_document(
    rules: Dict[str, Any]
) -> bool:

    paragraph_count = _safe_int(
        rules.get("paragraph_count")
    )

    heading_count = _safe_int(
        rules.get("heading_count")
    )

    table_count = _safe_int(
        rules.get("table_count")
    )

    image_count = _safe_int(
        rules.get("image_count")
    )

    shape_count = _safe_int(
        rules.get("shape_count")
    )

    text_content = normalize_text(
        rules.get("text_content", "")
    )

    if (
        paragraph_count == 0
        and heading_count == 0
        and table_count == 0
        and image_count == 0
        and shape_count == 0
        and not text_content
    ):
        return True

    return False


# ============================================================
# HEADING COMPARISON
# ============================================================

def compare_headings(
    master_rules: Dict[str, Any],
    student_rules: Dict[str, Any]
) -> List[Dict[str, Any]]:

    errors: List[Dict[str, Any]] = []

    master_headings = _safe_list(
        master_rules.get("headings")
    )

    student_headings = _safe_list(
        student_rules.get("headings")
    )

    master_count = len(master_headings)
    student_count = len(student_headings)

    # --------------------------------------------------------
    # Heading count
    # --------------------------------------------------------

    if student_count < master_count:

        errors.append(
            create_error(
                category="headings",
                message=(
                    f"Missing headings: expected {master_count}, "
                    f"found {student_count}."
                ),
                expected=master_count,
                actual=student_count,
                weight=1,
            )
        )

    elif student_count > master_count:

        errors.append(
            create_error(
                category="headings",
                message=(
                    f"Extra headings: expected {master_count}, "
                    f"found {student_count}."
                ),
                expected=master_count,
                actual=student_count,
                weight=1,
            )
        )

    # --------------------------------------------------------
    # Heading level distribution
    # --------------------------------------------------------

    def heading_levels(
        headings: List[Dict[str, Any]]
    ) -> Dict[str, int]:

        result: Dict[str, int] = {}

        for heading in headings:

            level = heading.get("level")

            if level is None:
                level = heading.get("heading_level")

            if level is None:
                continue

            level_key = str(level)

            result[level_key] = (
                result.get(level_key, 0) + 1
            )

        return result

    master_levels = heading_levels(
        master_headings
    )

    student_levels = heading_levels(
        student_headings
    )

    if master_levels != student_levels:

        errors.append(
            create_error(
                category="headings",
                message=(
                    "Heading level structure does not match "
                    "the master document."
                ),
                expected=master_levels,
                actual=student_levels,
                weight=1,
            )
        )

    return errors


# ============================================================
# TITLE STRUCTURE
# ============================================================

def compare_title_structure(
    master_rules: Dict[str, Any],
    student_rules: Dict[str, Any]
) -> List[Dict[str, Any]]:

    errors: List[Dict[str, Any]] = []

    master_headings = _safe_list(
        master_rules.get("headings")
    )

    student_headings = _safe_list(
        student_rules.get("headings")
    )

    def has_level_one(
        headings: List[Dict[str, Any]]
    ) -> bool:

        for heading in headings:

            level = heading.get("level")

            if level is None:
                level = heading.get("heading_level")

            try:

                if int(level) == 1:
                    return True

            except (TypeError, ValueError):
                pass

        return False

    master_has_title = has_level_one(
        master_headings
    )

    student_has_title = has_level_one(
        student_headings
    )

    if master_has_title and not student_has_title:

        errors.append(
            create_error(
                category="title",
                message=(
                    "The master document contains a title/"
                    "Heading 1, but the student document does not."
                ),
                expected=True,
                actual=False,
                weight=1,
            )
        )

    return errors


# ============================================================
# PARAGRAPH STRUCTURE
# ============================================================

def compare_paragraph_structure(
    master_rules: Dict[str, Any],
    student_rules: Dict[str, Any]
) -> List[Dict[str, Any]]:

    errors: List[Dict[str, Any]] = []

    master_paragraphs = _safe_list(
        master_rules.get("paragraphs")
    )

    student_paragraphs = _safe_list(
        student_rules.get("paragraphs")
    )

    # Get meaningful student text
    student_has_text = False

    for paragraph in student_paragraphs:

        if not isinstance(paragraph, dict):
            continue

        text = normalize_text(
            paragraph.get("text", "")
        )

        if text:
            student_has_text = True
            break

    # Get meaningful master text
    master_has_text = False

    for paragraph in master_paragraphs:

        if not isinstance(paragraph, dict):
            continue

        text = normalize_text(
            paragraph.get("text", "")
        )

        if text:
            master_has_text = True
            break

    if master_has_text and not student_has_text:

        errors.append(
            create_error(
                category="paragraphs",
                message=(
                    "The master document contains text, "
                    "but the student document has no meaningful text."
                ),
                expected="Meaningful text",
                actual="No meaningful text",
                weight=1,
            )
        )

    return errors


# ============================================================
# TABLE HELPERS
# ============================================================

def find_table_with_similar_structure(
    master_table: Dict[str, Any],
    student_tables: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Find a student table with a compatible column structure.

    Table name is intentionally ignored.
    Table location is intentionally ignored unless
    future comparison settings require strict location.
    """

    master_columns = _safe_int(
        master_table.get("column_count")
    )

    # First priority:
    # same number of columns
    for table in student_tables:

        student_columns = _safe_int(
            table.get("column_count")
        )

        if student_columns == master_columns:
            return table

    # Fallback:
    # any remaining table
    if student_tables:
        return student_tables[0]

    return None


def compare_tables(
    master_rules: Dict[str, Any],
    student_rules: Dict[str, Any]
) -> List[Dict[str, Any]]:

    errors: List[Dict[str, Any]] = []

    master_tables = _safe_list(
        master_rules.get("tables")
    )

    student_tables = _safe_list(
        student_rules.get("tables")
    )

    master_count = len(master_tables)
    student_count = len(student_tables)

    # --------------------------------------------------------
    # Table count
    # --------------------------------------------------------

    if student_count < master_count:

        errors.append(
            create_error(
                category="tables",
                message=(
                    f"Missing tables: expected {master_count}, "
                    f"found {student_count}."
                ),
                expected=master_count,
                actual=student_count,
                weight=1,
            )
        )

    elif student_count > master_count:

        errors.append(
            create_error(
                category="tables",
                message=(
                    f"Extra tables: expected {master_count}, "
                    f"found {student_count}."
                ),
                expected=master_count,
                actual=student_count,
                weight=1,
            )
        )

    # --------------------------------------------------------
    # Table structure
    # --------------------------------------------------------

    remaining_student_tables = list(
        student_tables
    )

    for master_table in master_tables:

        candidate = find_table_with_similar_structure(
            master_table,
            remaining_student_tables
        )

        if candidate is None:
            continue

        try:
            remaining_student_tables.remove(candidate)
        except ValueError:
            pass

        master_columns = _safe_int(
            master_table.get("column_count")
        )

        student_columns = _safe_int(
            candidate.get("column_count")
        )

        if master_columns != student_columns:

            errors.append(
                create_error(
                    category="tables",
                    message=(
                        "A table has an incorrect number "
                        "of columns."
                    ),
                    expected=master_columns,
                    actual=student_columns,
                    weight=1,
                )
            )

    return errors


# ============================================================
# IMAGE COMPARISON
# ============================================================

def compare_images(
    master_rules: Dict[str, Any],
    student_rules: Dict[str, Any]
) -> List[Dict[str, Any]]:

    errors: List[Dict[str, Any]] = []

    master_images = _safe_list(
        master_rules.get("images")
    )

    student_images = _safe_list(
        student_rules.get("images")
    )

    master_count = len(master_images)
    student_count = len(student_images)

    if student_count < master_count:

        errors.append(
            create_error(
                category="images",
                message=(
                    f"Missing images: expected {master_count}, "
                    f"found {student_count}."
                ),
                expected=master_count,
                actual=student_count,
                weight=1,
            )
        )

    elif student_count > master_count:

        errors.append(
            create_error(
                category="images",
                message=(
                    f"Extra images: expected {master_count}, "
                    f"found {student_count}."
                ),
                expected=master_count,
                actual=student_count,
                weight=1,
            )
        )

    # Image filename is intentionally ignored.
    # Image location is also intentionally ignored.

    return errors


# ============================================================
# SHAPE COMPARISON
# ============================================================

def compare_shapes(
    master_rules: Dict[str, Any],
    student_rules: Dict[str, Any]
) -> List[Dict[str, Any]]:

    errors: List[Dict[str, Any]] = []

    master_shapes = _safe_list(
        master_rules.get("shapes")
    )

    student_shapes = _safe_list(
        student_rules.get("shapes")
    )

    master_count = len(master_shapes)
    student_count = len(student_shapes)

    if student_count < master_count:

        errors.append(
            create_error(
                category="shapes",
                message=(
                    f"Missing shapes: expected {master_count}, "
                    f"found {student_count}."
                ),
                expected=master_count,
                actual=student_count,
                weight=1,
            )
        )

    elif student_count > master_count:

        errors.append(
            create_error(
                category="shapes",
                message=(
                    f"Extra shapes: expected {master_count}, "
                    f"found {student_count}."
                ),
                expected=master_count,
                actual=student_count,
                weight=1,
            )
        )

    # Shape type is intentionally ignored by default.

    return errors


# ============================================================
# FORMATTING COMPARISON
# ============================================================

def compare_formatting(
    master_rules: Dict[str, Any],
    student_rules: Dict[str, Any]
) -> List[Dict[str, Any]]:

    errors: List[Dict[str, Any]] = []

    master_formatting = (
        master_rules.get("formatting")
        or {}
    )

    student_formatting = (
        student_rules.get("formatting")
        or {}
    )

    # --------------------------------------------------------
    # Font names
    # --------------------------------------------------------

    master_fonts = set(
        normalize_text(font)
        for font in _safe_list(
            master_formatting.get("font_names")
        )
        if normalize_text(font)
    )

    student_fonts = set(
        normalize_text(font)
        for font in _safe_list(
            student_formatting.get("font_names")
        )
        if normalize_text(font)
    )

    if master_fonts:

        missing_fonts = (
            master_fonts - student_fonts
        )

        if missing_fonts:

            errors.append(
                create_error(
                    category="formatting",
                    message=(
                        "Some required font names "
                        "are missing."
                    ),
                    expected=sorted(master_fonts),
                    actual=sorted(student_fonts),
                    weight=1,
                )
            )

    # --------------------------------------------------------
    # Bold count
    # --------------------------------------------------------

    master_bold = _safe_int(
        master_formatting.get("bold_count")
    )

    student_bold = _safe_int(
        student_formatting.get("bold_count")
    )

    if student_bold < master_bold:

        errors.append(
            create_error(
                category="formatting",
                message=(
                    f"Missing bold formatting: expected at least "
                    f"{master_bold}, found {student_bold}."
                ),
                expected=master_bold,
                actual=student_bold,
                weight=1,
            )
        )

    # --------------------------------------------------------
    # Italic count
    # --------------------------------------------------------

    master_italic = _safe_int(
        master_formatting.get("italic_count")
    )

    student_italic = _safe_int(
        student_formatting.get("italic_count")
    )

    if student_italic < master_italic:

        errors.append(
            create_error(
                category="formatting",
                message=(
                    f"Missing italic formatting: expected at least "
                    f"{master_italic}, found {student_italic}."
                ),
                expected=master_italic,
                actual=student_italic,
                weight=1,
            )
        )

    # --------------------------------------------------------
    # Underline count
    # --------------------------------------------------------

    master_underline = _safe_int(
        master_formatting.get("underline_count")
    )

    student_underline = _safe_int(
        student_formatting.get("underline_count")
    )

    if student_underline < master_underline:

        errors.append(
            create_error(
                category="formatting",
                message=(
                    f"Missing underline formatting: expected at least "
                    f"{master_underline}, found {student_underline}."
                ),
                expected=master_underline,
                actual=student_underline,
                weight=1,
            )
        )

    # --------------------------------------------------------
    # Font size
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # Font size is intentionally NOT checked.
    #

    # --------------------------------------------------------
    # Alignment
    # --------------------------------------------------------

    master_alignments = set(
        normalize_text(value)
        for value in _safe_list(
            master_formatting.get("alignments")
        )
        if normalize_text(value)
    )

    student_alignments = set(
        normalize_text(value)
        for value in _safe_list(
            student_formatting.get("alignments")
        )
        if normalize_text(value)
    )

    if master_alignments:

        missing_alignments = (
            master_alignments - student_alignments
        )

        if missing_alignments:

            errors.append(
                create_error(
                    category="formatting",
                    message=(
                        "Some required paragraph alignments "
                        "are missing."
                    ),
                    expected=sorted(master_alignments),
                    actual=sorted(student_alignments),
                    weight=1,
                )
            )

    return errors


# ============================================================
# ALIGNMENT COMPARISON
# ============================================================

def compare_alignment(
    master_rules: Dict[str, Any],
    student_rules: Dict[str, Any]
) -> List[Dict[str, Any]]:

    # Alignment is already included in formatting
    # for the current analyzer.

    return []


# ============================================================
# MAIN DOCUMENT COMPARISON
# ============================================================

def compare_documents(
    master_rules: Dict[str, Any],
    student_rules: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare extracted Word rules.

    IMPORTANT:
    This function compares structure and formatting only.
    It does NOT calculate the final project score.

    The scoring/report layer remains responsible for
    converting errors into the project's final score.
    """

    if not isinstance(master_rules, dict):

        raise ValueError(
            "master_rules must be a dictionary."
        )

    if not isinstance(student_rules, dict):

        raise ValueError(
            "student_rules must be a dictionary."
        )

    errors: List[Dict[str, Any]] = []

    # --------------------------------------------------------
    # Empty document
    # --------------------------------------------------------

    if is_empty_document(student_rules):

        errors.append(
            create_error(
                category="document",
                message=(
                    "The student Word document is empty."
                ),
                expected="A non-empty Word document",
                actual="Empty document",
                weight=1,
            )
        )

        return {
            "success": False,
            "errors": errors,
            "error_count": len(errors),
            "passed": False,
        }

    # --------------------------------------------------------
    # Headings
    # --------------------------------------------------------

    errors.extend(
        compare_headings(
            master_rules,
            student_rules
        )
    )

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    errors.extend(
        compare_title_structure(
            master_rules,
            student_rules
        )
    )

    # --------------------------------------------------------
    # Paragraphs
    # --------------------------------------------------------

    errors.extend(
        compare_paragraph_structure(
            master_rules,
            student_rules
        )
    )

    # --------------------------------------------------------
    # Tables
    # --------------------------------------------------------

    errors.extend(
        compare_tables(
            master_rules,
            student_rules
        )
    )

    # --------------------------------------------------------
    # Images
    # --------------------------------------------------------

    errors.extend(
        compare_images(
            master_rules,
            student_rules
        )
    )

    # --------------------------------------------------------
    # Shapes
    # --------------------------------------------------------

    errors.extend(
        compare_shapes(
            master_rules,
            student_rules
        )
    )

    # --------------------------------------------------------
    # Formatting
    # --------------------------------------------------------

    errors.extend(
        compare_formatting(
            master_rules,
            student_rules
        )
    )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    total_errors = len(errors)

    passed = total_errors == 0

    return {
        "success": True,
        "errors": errors,
        "error_count": total_errors,
        "passed": passed,
        "checks": {
            "headings": True,
            "title": True,
            "paragraphs": True,
            "tables": True,
            "images": True,
            "shapes": True,
            "formatting": True,
        },
        "summary": {
            "master_heading_count": len(
                _safe_list(
                    master_rules.get("headings")
                )
            ),
            "student_heading_count": len(
                _safe_list(
                    student_rules.get("headings")
                )
            ),
            "master_table_count": len(
                _safe_list(
                    master_rules.get("tables")
                )
            ),
            "student_table_count": len(
                _safe_list(
                    student_rules.get("tables")
                )
            ),
            "master_image_count": len(
                _safe_list(
                    master_rules.get("images")
                )
            ),
            "student_image_count": len(
                _safe_list(
                    student_rules.get("images")
                )
            ),
            "master_shape_count": len(
                _safe_list(
                    master_rules.get("shapes")
                )
            ),
            "student_shape_count": len(
                _safe_list(
                    student_rules.get("shapes")
                )
            ),
        },
    }


# ============================================================
# COMPARE WORD FILES
# ============================================================

def compare_word_files(
    master_filepath: str,
    student_filepath: str
) -> Dict[str, Any]:
    """
    Backward-compatible helper.

    Extracts rules from both DOCX files and compares them.
    """

    master_rules = extract_full_rules(
        master_filepath
    )

    student_rules = extract_full_rules(
        student_filepath
    )

    result = compare_documents(
        master_rules,
        student_rules
    )

    result["master_file"] = str(
        master_filepath
    )

    result["student_file"] = str(
        student_filepath
    )

    return result


# ============================================================
# CREATE MASTER RULES DIRECTLY FROM DOCX
# ============================================================

def create_master_rules_from_word(
    master_filepath: str,
    project_id: Any
) -> Dict[str, Any]:
    """
    Extract a Word document and save its rules
    as the Master rules for the given project.
    """

    master_rules = extract_full_rules(
        master_filepath
    )

    saved_path = save_master_rules(
        master_rules,
        project_id
    )

    return {
        "success": True,
        "project_id": str(project_id),
        "master_rules_path": saved_path,
        "master_rules": master_rules,
    }


# ============================================================
# GRADE STUDENT AGAINST STORED MASTER
# ============================================================

def compare_student_with_master(
    student_filepath: str,
    project_id: Any
) -> Dict[str, Any]:
    """
    Load the stored Word master rules and compare
    the student Word document against them.
    """

    master_rules = load_master_rules(
        project_id
    )

    if master_rules is None:

        return {
            "success": False,
            "project_id": str(project_id),
            "errors": [
                create_error(
                    category="master",
                    message=(
                        f"No Word master project found "
                        f"for Project {project_id}."
                    ),
                    weight=1,
                )
            ],
            "error_count": 1,
            "passed": False,
        }

    student_rules = extract_full_rules(
        student_filepath
    )

    result = compare_documents(
        master_rules,
        student_rules
    )

    result["project_id"] = str(
        project_id
    )

    result["student_file"] = str(
        student_filepath
    )

    return result


# ============================================================
# PRINT RESULT
# ============================================================

def print_comparison_result(
    result: Dict[str, Any]
) -> None:

    print("\n" + "=" * 60)
    print("WORD DOCUMENT COMPARISON")
    print("=" * 60)

    print(
        f"Success: {result.get('success')}"
    )

    print(
        f"Errors: {result.get('error_count', 0)}"
    )

    print(
        f"Passed: {result.get('passed')}"
    )

    errors = result.get(
        "errors",
        []
    )

    if not errors:

        print("\n✅ No structural errors found.")

    else:

        print("\nErrors:")

        for index, error in enumerate(
            errors,
            start=1
        ):

            print(
                f"{index}. "
                f"[{error.get('category', 'unknown')}] "
                f"{error.get('message', '')}"
            )

    print("=" * 60)


# ============================================================
# JSON REPORT HELPER
# ============================================================

def save_comparison_result(
    result: Dict[str, Any],
    output_path: str
) -> str:

    output_file = Path(
        output_path
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2
        )

    return str(output_file)


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Word Rule Engine test"
    )

    master_file = Path(
        "master_project.docx"
    )

    student_file = Path(
        "student_project.docx"
    )

    if (
        master_file.exists()
        and student_file.exists()
    ):

        result = compare_word_files(
            str(master_file),
            str(student_file)
        )

        print_comparison_result(
            result
        )

    else:

        print(
            "⚠️ Test files not found."
        )

        print(
            "Expected:"
        )

        print(
            f"  - {master_file}"
        )

        print(
            f"  - {student_file}"
        )