import re

def extract_keywords(text):
    text = text.lower()
    return set(re.findall(r"[a-zA-Z]+", text))


def match_users(description, users):
    """
    users = {
        "Alice": [{"skill": "python", "level": "advanced"}, ...]
    }
    """
    desc_keywords = extract_keywords(description)
    results = []

    for name, skills in users.items():
        user_skills = {s["skill"].lower() for s in skills}
        matched = desc_keywords & user_skills

        if matched:
            score = len(matched)
            results.append({
                "name": name,
                "score": score,
                "matched": list(matched)
            })

    return sorted(results, key=lambda x: x["score"], reverse=True)
