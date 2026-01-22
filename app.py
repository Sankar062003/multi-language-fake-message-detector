from flask import Flask, render_template, request
import pickle
# Legitimate bank-style phrases (to avoid false positives)
legit_bank_phrases = [
    "dear customer",
    "this is an automated message",
    "do not share otp",
    "bank never asks",
    "no otp",
    "no pin",
    "visit nearest branch",
    "contact official bank",
    "no link",
    "no action required"
]
def looks_legitimate(text):
    text_lower = text.lower()

    legit_hits = 0
    for phrase in legit_bank_phrases:
        if phrase in text_lower:
            legit_hits += 1

    has_link = "http://" in text_lower or "https://" in text_lower or "www." in text_lower

    # If message looks official AND has no links → REAL
    if legit_hits >= 2 and not has_link:
        return True

    return False
import re
def translate_to_english(text):
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except:
        return text

app = Flask(__name__)

# Load model & vectorizer
model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vector.pkl", "rb"))

# -------- TRANSLATION -------- #
def translate_to_english(text):
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except:
        return text

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

    # STEP 1: Legit override FIRST
    if looks_legitimate(message):
        return render_template(
            "index.html",
            result="✅ REAL MESSAGE",
            reason="Official informational message with no scam indicators",
            language="Detected Automatically"
        )

    # STEP 2: Detect language
    try:
        lang = detect(message)
    except:
        lang = "en"

    # STEP 3: Suspicious link check
    if contains_suspicious_link(message):
        return render_template(
            "index.html",
            result="❌ FAKE MESSAGE",
            reason="Suspicious link detected",
            language=lang
        )

    # STEP 4: Native language scam words
    if contains_language_scam(message, lang):
        return render_template(
            "index.html",
            result="❌ FAKE MESSAGE",
            reason="Scam pattern detected in native language",
            language=lang
        )

    # STEP 5: Translate for ML
    if lang != "en":
        message = translate_to_english(message)

    # STEP 6: ML prediction
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
    app.run()
