# ============================================================
# WORD AI FEEDBACK ENGINE
# ============================================================
#
# Purpose:
#   Generate optional AI-powered explanations for Word
#   document grading results.
#
# IMPORTANT:
#   AI does NOT:
#       - calculate the score
#       - detect errors
#       - change deductions
#       - decide pass/fail
#
#   The Rule Engine and Scoring Engine are the authority.
#
#   AI only makes the verified feedback easier for students
#   to understand.
#
# ============================================================

import os
import json

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
# ============================================================
# CONFIGURATION
# ============================================================

# Groq can use the OpenAI-compatible API.
#
# You can set:
#
# GROQ_API_KEY
#
# in your .env file or environment variables.

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

DEFAULT_MODEL = "openai/gpt-oss-20b"


# ============================================================
# CREATE CLIENT
# ============================================================

def get_ai_client():
    """
    Create the AI client.

    Returns None if the API key is not available.
    """

    if not GROQ_API_KEY:
        return None

    try:

        return OpenAI(
            api_key=GROQ_API_KEY,
            base_url=GROQ_BASE_URL,
        )

    except Exception as e:

        print(
            f"⚠️ Word AI client creation failed: {e}"
        )

        return None


# ============================================================
# FORMAT FEEDBACK FOR AI
# ============================================================

def prepare_feedback_for_ai(feedback):
    """
    Convert deterministic feedback into a compact structure
    that can safely be sent to the AI.
    """

    prepared = []

    if not feedback:
        return prepared

    for item in feedback:

        prepared.append({

            "title": item.get(
                "title",
                ""
            ),

            "message": item.get(
                "message",
                ""
            ),

            "reason": item.get(
                "reason",
                ""
            ),

            "correction": item.get(
                "correction",
                ""
            ),

            "marks_lost": item.get(
                "marks_lost",
                0
            ),

            "severity": item.get(
                "severity",
                "medium"
            ),

        })

    return prepared


# ============================================================
# BUILD PROMPT
# ============================================================

def build_prompt(
    score,
    max_score,
    status,
    passed,
    feedback,
):
    """
    Create the prompt sent to the AI.

    The prompt explicitly prevents the AI from changing
    grading decisions.
    """

    feedback_data = prepare_feedback_for_ai(
        feedback
    )

    feedback_json = json.dumps(
        feedback_data,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are an educational feedback assistant.

You are helping a student understand the result of a
Microsoft Word project.

IMPORTANT RULES:

1. Do NOT calculate the score.
2. Do NOT change the score.
3. Do NOT add new errors.
4. Do NOT remove errors.
5. Do NOT change the number of points lost.
6. Do NOT change pass/fail status.
7. Only explain the verified feedback provided below.
8. Do not mention internal software, Rule Engine, Scoring
   Engine, Python, API, or programming details.
9. Use simple and encouraging English.
10. Do not shame or criticize the student.
11. Focus on what the student can improve.
12. If there are no errors, congratulate the student.
13. Font size is NOT a grading requirement. Never mention
    font size as a problem.

VERIFIED RESULT:

Score: {score}/{max_score}
Status: {status}
Passed: {passed}

VERIFIED FEEDBACK:

{feedback_json}

Write a short student-friendly explanation.

Structure:

1. Start with one short sentence about the overall result.
2. Mention the most important areas that need improvement.
3. Explain what the student should do next.
4. End with an encouraging sentence.

Do not invent any information.
"""

    return prompt


# ============================================================
# GENERATE AI FEEDBACK
# ============================================================

def generate_ai_feedback(
    score,
    max_score,
    status,
    passed,
    feedback,
    model=DEFAULT_MODEL,
):
    """
    Generate AI-enhanced Word feedback.

    Returns:
        string
        or None if AI is unavailable.
    """

    # --------------------------------------------------------
    # No feedback
    # --------------------------------------------------------

    if not feedback:

        return (
            "Excellent work! Your Word document met all "
            "of the checked project requirements. "
            "Keep up the good work."
        )


    # --------------------------------------------------------
    # Create client
    # --------------------------------------------------------

    client = get_ai_client()

    if client is None:

        print(
            "⚠️ Word AI feedback unavailable: "
            "GROQ_API_KEY is not configured."
        )

        return None


    # --------------------------------------------------------
    # Build prompt
    # --------------------------------------------------------

    prompt = build_prompt(
        score=score,
        max_score=max_score,
        status=status,
        passed=passed,
        feedback=feedback,
    )


    # --------------------------------------------------------
    # Call AI
    # --------------------------------------------------------

    try:

        response = client.chat.completions.create(

            model=model,

            messages=[

                {
                    "role": "system",
                    "content": (
                        "You are a helpful educational "
                        "feedback assistant."
                    ),
                },

                {
                    "role": "user",
                    "content": prompt,
                },

            ],

            temperature=0.3,

            max_tokens=500,
        )


        # ----------------------------------------------------
        # Extract response
        # ----------------------------------------------------

        if not response.choices:

            print(
                "⚠️ Word AI returned no choices."
            )

            return None


        ai_text = (
            response
            .choices[0]
            .message
            .content
        )


        if not ai_text:

            print(
                "⚠️ Word AI returned empty feedback."
            )

            return None


        return ai_text.strip()


    except Exception as e:

        print(
            f"⚠️ Word AI feedback failed: {e}"
        )

        return None


# ============================================================
# GENERATE COMPLETE FEEDBACK
# ============================================================

def generate_ai_enhanced_feedback(
    errors,
    score_details,
    deterministic_feedback,
    model=DEFAULT_MODEL,
):
    """
    Combine deterministic feedback with optional AI feedback.

    The deterministic scoring result remains authoritative.
    """

    score = score_details.get(
        "final_score",
        0
    )

    max_score = 20

    status = score_details.get(
        "status",
        "FAILED"
    )

    passed = score_details.get(
        "passed",
        False
    )


    ai_feedback = generate_ai_feedback(

        score=score,

        max_score=max_score,

        status=status,

        passed=passed,

        feedback=deterministic_feedback,

        model=model,
    )


    return {

        "deterministic_feedback": (
            deterministic_feedback
        ),

        "ai_feedback": ai_feedback,

        "ai_available": (
            ai_feedback is not None
        ),
    }


# ============================================================
# SIMPLE TEST
# ============================================================

if __name__ == "__main__":

    test_feedback = [

        {
            "error_type": "missing_heading",

            "category": "structure",

            "title": "Required section is missing",

            "message": (
                "2 required heading(s) are missing."
            ),

            "reason": (
                "Some required sections or headings "
                "were not found."
            ),

            "correction": (
                "Review the project instructions and "
                "add the missing sections."
            ),

            "marks_lost": 1,

            "severity": "medium",
        },

        {
            "error_type": "missing_table",

            "category": "tables",

            "title": "Required table is missing",

            "message": (
                "1 required table is missing."
            ),

            "reason": (
                "The project requires a table."
            ),

            "correction": (
                "Add the required table to the document."
            ),

            "marks_lost": 2,

            "severity": "high",
        },

        {
            "error_type": "missing_image",

            "category": "visual",

            "title": "Required image is missing",

            "message": (
                "1 required image is missing."
            ),

            "reason": (
                "The project requires an image."
            ),

            "correction": (
                "Add the required image."
            ),

            "marks_lost": 1,

            "severity": "medium",
        },

        {
            "error_type": "wrong_font",

            "category": "formatting",

            "title": "Font formatting needs adjustment",

            "message": (
                "Required font is not being used."
            ),

            "reason": (
                "The required font was not found."
            ),

            "correction": (
                "Use the font required by the project."
            ),

            "marks_lost": 1,

            "severity": "low",
        },
    ]


    test_score_details = {

        "final_score": 15,

        "status": "GOOD",

        "passed": True,

        "total_deduction": 5,
    }


    result = generate_ai_enhanced_feedback(

        errors=[],

        score_details=test_score_details,

        deterministic_feedback=test_feedback,
    )


    print()
    print("=" * 70)
    print("WORD AI FEEDBACK TEST")
    print("=" * 70)

    print(
        f"AI Available: "
        f"{result['ai_available']}"
    )

    print()

    if result["ai_feedback"]:

        print(
            result["ai_feedback"]
        )

    else:

        print(
            "AI feedback is unavailable."
        )

    print("=" * 70)