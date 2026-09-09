import os
import json
from google.oauth2 import service_account


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]


def get_credentials():
    """
    Get Google credentials from Render environment variable.
    """

    credentials_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if not credentials_json:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON environment variable is not set."
        )

    try:
        credentials_info = json.loads(credentials_json)

    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Invalid GOOGLE_SERVICE_ACCOUNT_JSON: {e}"
        )

    return service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=SCOPES
    )