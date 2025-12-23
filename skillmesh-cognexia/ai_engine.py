import gspread
from google.oauth2.service_account import Credentials
import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "credentials/service_account.json",
    scopes=SCOPES
)

client = gspread.authorize(creds)

def extract_skills(text):
    keywords = [
        "python","java","ai","ml","flask","react",
        "cloud","devops","html","css","javascript"
    ]
    text = text.lower()
    return [k for k in keywords if k in text]


def match_users(request_text, users_skills):
    req_skills = extract_skills(request_text)
    results = []

    for user, skills in users_skills.items():
        skill_names = [s["skill"].lower() for s in skills]
        common = set(req_skills) & set(skill_names)

        if common:
            score = int((len(common) / len(req_skills)) * 100) if req_skills else 0
            results.append({
                "name": user,
                "score": score,
                "matched": list(common)
            })

    return sorted(results, key=lambda x: x["score"], reverse=True)
