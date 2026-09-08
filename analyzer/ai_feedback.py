import os

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

API_KEY = os.getenv("GROQ_API_KEY")

print(
    "DEBUG - GROQ_API_KEY loaded:",
    bool(API_KEY)
)

if not API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY environment variable is not set."
    )


client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


# ============================================================
# AI FEEDBACK
# ============================================================

def generate_ai_feedback(errors, error_deductions=None):
    """
    Generate Persian student feedback from VERIFIED grading results.

    AI only explains:
    - What the problem was
    - Why it was a problem
    - How many marks were lost

    AI does NOT:
    - calculate marks
    - change marks
    - invent errors
    - give repair instructions
    """

    if not errors:
        return "هیچ مشکلی در پروژه شما پیدا نشد. آفرین!"

    if error_deductions is None:
        error_deductions = []

    verified_items = []

    for i, error in enumerate(errors):

        deduction_info = (
            error_deductions[i]
            if i < len(error_deductions)
            else {}
        )

        verified_items.append({
            "problem": error,
            "marks_lost": deduction_info.get(
                "deduction",
                0
            )
        })

    error_text = "\n".join(
        f"""
Problem:
{item["problem"]}

Verified marks lost:
{item["marks_lost"]}
"""
        for item in verified_items
    )

    prompt = f"""
You are an educational feedback assistant for an Excel
grading system.

IMPORTANT:
The errors and marks below were already verified by a
deterministic grading system.

Your ONLY job is to explain the verified results to the
student in simple Persian.

For each problem, explain ONLY:

1. What was wrong.
2. Why it was a problem.
3. How many marks were lost.

STRICT RULES:

- Write the entire response in Persian.
- Do NOT give instructions for fixing the Excel file.
- Do NOT tell the student to delete anything.
- Do NOT tell the student to add anything.
- Do NOT tell the student to rename anything.
- Do NOT tell the student to move anything.
- Do NOT tell the student to create or rebuild a table.
- Do NOT provide a step-by-step repair process.
- Do NOT calculate marks yourself.
- Do NOT change the verified marks.
- Do NOT invent any error.
- Do NOT remove any error.
- Use exactly the verified marks provided below.
- If the verified marks are 0, clearly say that no marks
  were lost for that specific error.
- Keep the explanation concise and student-friendly.

Use this structure:

مشکل:
...

علت:
...

نمره از دست‌رفته:
... نمره

Verified grading information:
{error_text}
"""

    try:

        response = client.responses.create(
            model="openai/gpt-oss-20b",
            input=prompt
        )

        return response.output_text

    except Exception as e:

        print(
            f"⚠️ AI feedback generation failed: {e}"
        )

        return None


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("AI FEEDBACK ENGINE TEST")
    print("=" * 60)

    test_errors = [

        {
            "type": "missing_column",
            "sheet": "Sheet2",
            "column": "اسم محصول"
        },

        {
            "type": "missing_data",
            "sheet": "Sheet2",
            "expected_rows": 5,
            "actual_rows": 0,
            "missing_rows": 5
        }

    ]

    feedback = generate_ai_feedback(
        test_errors
    )

    print()

    if feedback:

        print(feedback)

    else:

        print(
            "⚠️ AI feedback unavailable."
        )

