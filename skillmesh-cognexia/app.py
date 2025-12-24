from flask import Flask, render_template, request, redirect
import gspread
from google.oauth2.service_account import Credentials
from ai_engine import match_users
import os
import json

app = Flask(__name__)

# -------- GOOGLE SHEETS AUTH (ENV SAFE) --------
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_json = json.loads(os.environ["GOOGLE_CREDS"])
creds = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
client = gspread.authorize(creds)

sheet = client.open("SkillMeshDB")
users_ws = sheet.worksheet("users")
skills_ws = sheet.worksheet("skills")

# ---------------- ROUTES ----------------

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

        users_ws.append_row([name, bio, email, phone])

        for s, l in zip(skills, levels):
            skills_ws.append_row([name, s, l])

        return redirect("/dashboard")

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

        raw = match_users(desc, users)

        for m in raw:
            u = next(x for x in users_data if x["name"] == m["name"])
            matches.append({
                "name": m["name"],
                "score": m["score"],
                "matched": m["matched"],
                "email": u["email"],
                "phone": u["phone"]
            })

    return render_template("request.html", matches=matches)


@app.route("/dashboard")
def dashboard():
    users = users_ws.get_all_records()
    skills = skills_ws.get_all_records()

    total_users = len(users)
    total_skills = len(skills)

    skill_count = {}
    for s in skills:
        skill_count[s["skill"]] = skill_count.get(s["skill"], 0) + 1

    top_skills = sorted(skill_count.items(), key=lambda x: x[1], reverse=True)[:5]
    recent_users = users[-5:]

    return render_template(
        "dashboard.html",
        total_users=total_users,
        total_skills=total_skills,
        top_skills=top_skills,
        recent_users=recent_users
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
