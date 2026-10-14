
import json
import os

import firebase_admin
from firebase_admin import credentials, firestore


def get_firestore():
    service_account_json = os.environ.get(
        "FIREBASE_SERVICE_ACCOUNT_JSON"
    )

    if not service_account_json:
        raise RuntimeError(
            "FIREBASE_SERVICE_ACCOUNT_JSON is not configured"
        )

    if not firebase_admin._apps:
        service_account_info = json.loads(
            service_account_json
        )

        credential = credentials.Certificate(
            service_account_info
        )

        firebase_admin.initialize_app(credential)

    return firestore.client()
