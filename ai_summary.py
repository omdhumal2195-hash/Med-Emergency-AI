"""Local ML/NLP summary using TF-IDF sentence ranking.
This summarizes only user-entered facts; it does not diagnose or recommend treatment.
"""
import re
from sklearn.feature_extraction.text import TfidfVectorizer

def generate_medical_summary(name, profile, public=False):
    facts = []
    if profile.get("blood_group") and (not public or profile.get("show_blood_group")):
        facts.append(f"Blood group: {profile['blood_group']}.")
    if profile.get("allergies") and (not public or profile.get("show_allergies")):
        facts.append(f"Reported drug allergies: {profile['allergies']}.")
    if profile.get("medicines") and (not public or profile.get("show_medicines")):
        facts.append(f"Current medicines: {profile['medicines']}.")
    if profile.get("medicine_name") and (not public or profile.get("show_medicines")):
        medication = profile["medicine_name"]
        if profile.get("medicine_dose"):
            medication += f", dose: {profile['medicine_dose']}"
        if profile.get("medicine_frequency"):
            medication += f", frequency: {profile['medicine_frequency']}"
        if profile.get("medicine_time"):
            medication += f", time: {profile['medicine_time']}"
        facts.append(f"Medication schedule: {medication}.")
    if profile.get("history") and (not public or profile.get("show_history")):
        facts.append(f"Medical history: {profile['history']}.")
    if profile.get("age") and (not public or profile.get("show_age")):
        facts.append(f"Age: {profile['age']}.")
    if not facts:
        return "No medical details have been added or selected for emergency display."
    # TF-IDF ranks the patient's own short medical facts by term importance.
    # For very short profiles, preserve all facts rather than dropping information.
    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(facts)
        scores = matrix.sum(axis=1).A1
        ranked = sorted(range(len(facts)), key=lambda i: scores[i], reverse=True)
        selected = [facts[i] for i in ranked[:min(4, len(facts))]]
        return f"Emergency summary for {name}: " + " ".join(selected)
    except ValueError:
        return f"Emergency summary for {name}: " + " ".join(facts)

if __name__ == "__main__":
    demo = {"blood_group":"O+", "allergies":"Penicillin (reported)", "medicines":"As entered by patient"}
    print(generate_medical_summary("Demo Patient", demo))
