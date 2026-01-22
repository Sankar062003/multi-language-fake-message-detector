from flask import Flask, render_template, request
import pickle
import re
from langdetect import detect
from deep_translator import GoogleTranslator

app = Flask(__name__)

# -------- LOAD MODEL --------
model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vector.pkl", "rb"))

# -------- TRANSLATION --------
def translate_to_english(text):
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except:
        return text

# -------- RULE BASED CHECKS --------
def contains_suspicious_link(text):
    return bool(re.search(r"http[s]?://|www\.|\.xyz|\.top|\.online|\.site", text.lower()))

telugu_scam_words = [
    "డబ్బు వచ్చింది",
    "లింక్ ఓపెన్ చేయండి",
    "మీకు కూడా వస్తుంది",
    "ప్రయత్నించి చూడండి"
]

hindi_scam_words = [
    "मुझे पैसे मिले",
    "आपको भी मिलेगा",
    "लिंक खोलें",
    "अभी क्लिक करें"
]

def contains_language_scam(text, lang):
    if lang == "te":
        return any(word in text for word in telugu_scam_words)
    if lang == "hi":
        return any(word in text for word in hindi_scam_words)
    return False

# -------- ROUTES --------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    message = request.form["message"]

    # 1️⃣ Detect language
    try:
        lang = detect(message)
    except:
        lang = "en"

    # 2️⃣ Hard scam rules (ALWAYS FIRST)
    if contains_suspicious_link(message):
        return render_template(
            "index.html",
            result="❌ FAKE MESSAGE",
            reason="Suspicious link detected",
            language=lang
        )

    if contains_language_scam(message, lang):
        return render_template(
            "index.html",
            result="❌ FAKE MESSAGE",
            reason="Scam pattern detected in native language",
            language=lang
        )

    # 3️⃣ Translate for ML
    message_en = translate_to_english(message) if lang != "en" else message

    # 4️⃣ ML Prediction (FINAL DECISION)
    data = vectorizer.transform([message_en])
    prediction = model.predict(data)[0]

    if prediction == 1:
        result = "✅ REAL MESSAGE"
        reason = "ML model classified as legitimate"
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
