from flask import Flask, render_template, request, redirect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from ai_engine import match_users
import gspread
from google.oauth2.service_account import Credentials
import os
app = Flask(__name__)

# ---------------- GOOGLE SHEETS SETUP ----------------
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "credentials/service_account.json",
    scopes=SCOPES
)

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

        print("DEBUG skills:", skills)
        print("DEBUG levels:", levels)

        # Add user
        users_ws.append_row([name, bio, email, phone])

        # Add skills (only if checkbox selected)
        for skill, level in zip(skills, levels):
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

    skill_count = {}
    for row in skills_data:
        skill_count[row["skill"]] = skill_count.get(row["skill"], 0) + 1

    top_skills = dict(sorted(skill_count.items(), key=lambda x: x[1], reverse=True)[:5])

    return render_template(
        "dashboard.html",
        total_users=total_users,
        top_skills=top_skills
    )



if __name__ == "__main__":
    import os
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
