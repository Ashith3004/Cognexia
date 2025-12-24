from flask import Flask, render_template, request, redirect
import gspread
from google.oauth2.service_account import Credentials
import os
from ai_engine import match_users

app = Flask(__name__)

# ================== GOOGLE SHEETS CONFIG ==================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Credentials from ENV (Render-safe)
creds = Credentials.from_service_account_info(
    {
        "type": "service_account",
        "project_id": os.environ.get("PROJECT_ID"),
        "private_key_id": os.environ.get("PRIVATE_KEY_ID"),
        "private_key": os.environ.get("PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.environ.get("CLIENT_EMAIL"),
        "client_id": os.environ.get("CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.environ.get("CLIENT_CERT_URL"),
    },
    scopes=SCOPES
)

client = gspread.authorize(creds)
sheet = client.open("SkillMeshDB")
users_ws = sheet.worksheet("users")
skills_ws = sheet.worksheet("skills")

# ================== ROUTES ==================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        name = request.form["name"]
        bio = request.form["bio"]
        email = request.form["email"]
        phone = request.form["phone"]

        skills = request.form.getlist("skill")
        levels = request.form.getlist("level")

        # Store user
        users_ws.append_row([name, bio, email, phone])

        # Store skills
        for skill, level in zip(skills, levels):
            if skill.strip():
                skills_ws.append_row([name, skill, level])

        return redirect("/")

    return render_template("profile.html")


@app.route("/request", methods=["GET", "POST"])
def help_request():
    matches = []

    if request.method == "POST":
        desc = request.form["desc"]

        skills_data = skills_ws.get_all_records()
        users_data = users_ws.get_all_records()

        users = {}
        for row in skills_data:
            users.setdefault(row["name"], []).append({
                "skill": row["skill"],
                "level": row["level"]
            })

        raw_matches = match_users(desc, users)

        for m in raw_matches:
            user = next(u for u in users_data if u["name"] == m["name"])
            matches.append({
                "name": m["name"],
                "score": m["score"],
                "matched": m["matched"],
                "email": user["email"],
                "phone": user["phone"]
            })

    return render_template("request.html", matches=matches)


@app.route("/dashboard")
def dashboard():
    skills_data = skills_ws.get_all_records()
    users_data = users_ws.get_all_records()

    total_users = len(users_data)

    # Count skills
    skill_count = {}
    for row in skills_data:
        skill = row.get("skill")
        if skill:
            skill_count[skill] = skill_count.get(skill, 0) + 1

    # Convert to LIST (IMPORTANT FIX)
    top_skills = sorted(skill_count.items(), key=lambda x: x[1], reverse=True)

    recent_users = users_data[-5:] if len(users_data) >= 5 else users_data

    return render_template(
        "dashboard.html",
        total_users=total_users,
        top_skills=top_skills,
        recent_users=recent_users
    )


# ================== RUN ==================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=True
    )
