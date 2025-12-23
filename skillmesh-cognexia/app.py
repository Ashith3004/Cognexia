from flask import Flask, render_template, request, redirect
from ai_engine import match_users
import json
import os
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    service_account_info = json.loads(
        os.environ["GOOGLE_CREDS_JSON"]
    )

    creds = Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES
    )

    client = gspread.authorize(creds)
    sheet = client.open("SkillMeshDB")

    users_ws = sheet.worksheet("users")
    skills_ws = sheet.worksheet("skills")

except Exception as e:
    print("❌ Google Sheets connection error:", e)
    users_ws = None
    skills_ws = None



# ---------------- ROUTES ----------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        if not users_ws or not skills_ws:
            return "Database connection error", 500

        name = request.form.get("name")
        bio = request.form.get("bio")
        email = request.form.get("email")
        phone = request.form.get("phone")

        skills = request.form.getlist("skill")
        levels = request.form.getlist("level")

        # Add user
        users_ws.append_row([name, bio, email, phone])

        # Add skills safely
        for i in range(len(skills)):
            skill = skills[i]
            level = levels[i] if i < len(levels) else "Beginner"
            skills_ws.append_row([name, skill, level])

        return redirect("/")

    return render_template("profile.html")


@app.route("/request", methods=["GET", "POST"])
def help_request():
    matches = []

    if request.method == "POST":
        if not users_ws or not skills_ws:
            return "Database connection error", 500

        desc = request.form.get("desc")

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
            user = next((u for u in users_data if u["name"] == m["name"]), None)
            if user:
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
    if not users_ws or not skills_ws:
        return "Database connection error", 500

    skills_data = skills_ws.get_all_records()
    users_data = users_ws.get_all_records()

    total_users = len(users_data)

    skill_count = {}
    for row in skills_data:
        skill = row["skill"]
        skill_count[skill] = skill_count.get(skill, 0) + 1

    top_skills = dict(
        sorted(skill_count.items(), key=lambda x: x[1], reverse=True)[:5]
    )

    return render_template(
        "dashboard.html",
        total_users=total_users,
        top_skills=top_skills
    )


# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_ENV") == "development"
    )

