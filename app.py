from flask import Flask, render_template, request
import pickle
import re
from langdetect import detect
from googletrans import Translator

app = Flask(__name__)
translator = Translator()

model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vector.pkl", "rb"))

# -------- RULE BASED CHECKS -------- #

def contains_suspicious_link(text):
    return bool(re.search(r"http[s]?://|www\.|\.xyz|\.top|\.online|\.site", text))

telugu_scam_words = [
    "నిజంగా నాకు వచ్చింది",
    "మీకు కూడా వస్తుంది",
    "ప్రయత్నించి చూడండి",
    "డబ్బు వచ్చింది",
    "లింక్ ఓపెన్ చేయండి"
]

hindi_scam_words = [
    "मुझे पैसे मिले",
    "आपको भी मिलेगा",
    "लिंक खोलें",
    "अभी क्लिक करें",
    "₹"
]

def contains_language_scam(text, lang):
    if lang == "te":
        return any(word in text for word in telugu_scam_words)
    if lang == "hi":
        return any(word in text for word in hindi_scam_words)
    return False

# -------- ROUTES -------- #

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    message = request.form["message"]

    try:
        lang = detect(message)
    except:
        lang = "en"

    # RULE 1: Suspicious link
    if contains_suspicious_link(message):
        return render_template(
            "index.html",
            result="❌ FAKE MESSAGE",
            reason="Suspicious link detected",
            language=lang
        )

    # RULE 2: Language specific scam words
    if contains_language_scam(message, lang):
        return render_template(
            "index.html",
            result="❌ FAKE MESSAGE",
            reason="Scam pattern detected in native language",
            language=lang
        )

    # TRANSLATE to English for ML
    if lang != "en":
        message = translator.translate(message, dest="en").text

    data = vectorizer.transform([message])
    prediction = model.predict(data)[0]

    if prediction == 1:
        result = "✅ REAL MESSAGE"
        reason = "No scam patterns detected"
    else:
        result = "❌ FAKE MESSAGE"
        reason = "ML model classified as scam"

    return render_template(
        "index.html",
        result=result,
        reason=reason,
        language=lang
    )

if __name__ == "__main__":
    app.run(debug=True)
