from flask import redirect
from flask import Flask, render_template, request
import pickle
import re
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator

app = Flask(__name__)

# -------- LOAD MODEL --------
model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vector.pkl", "rb"))

# -------- SAFE TRANSLATION --------
def translate_to_english(text):
    try:
        translated = GoogleTranslator(source="auto", target="en").translate(text)
        return translated if translated else text
    except:
        return text

# -------- STRONG LINK DETECTION --------
def contains_suspicious_link(text):
    link_patterns = [
        r"http[s]?://",
        r"www\.",
        r"\.xyz",
        r"\.top",
        r"\.online",
        r"\.site",
        r"\.click",
        r"\.link",
        r"bit\.ly",
        r"tinyurl",
    ]
    return any(re.search(p, text.lower()) for p in link_patterns)

# -------- COMMON SCAM WORDS (ANY DOMAIN) --------
scam_keywords = [
    "click here",
    "open link",
    "free",
    "offer",
    "limited time",
    "urgent",
    "winner",
    "claim now",
    "verify now",
    "congratulations",
    "lottery",
    "investment",
    "profit",
    "bonus"
]

def contains_scam_keywords(text):
    text = text.lower()
    return any(word in text for word in scam_keywords)

# -------- ROUTES --------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["GET", "POST"])
def predict():
    if request.method == "GET":
        return redirect("/")

    message = request.form.get("message", "").strip()

    # Empty message safety
    if not message:
        return render_template(
            "index.html",
            result="⚠️ ENTER A MESSAGE",
            reason="Message cannot be empty",
            language="unknown"
        )

    # 1️⃣ Language detection (SAFE)
    try:
        lang = detect(message)
    except LangDetectException:
        lang = "en"

    # 2️⃣ HARD RULES (OVERRIDE ML)
    if contains_suspicious_link(message):
        return render_template(
            "index.html",
            result="❌ FAKE MESSAGE",
            reason="Suspicious link detected",
            language=lang
        )

    if contains_scam_keywords(message):
        return render_template(
            "index.html",
            result="❌ FAKE MESSAGE",
            reason="Common scam keywords detected",
            language=lang
        )

    # 3️⃣ Translate if needed
    message_en = translate_to_english(message) if lang != "en" else message

    # Final safety
    if not message_en.strip():
        message_en = message

    # 4️⃣ ML Prediction
    try:
        data = vectorizer.transform([message_en])
        prediction = model.predict(data)[0]
    except:
        return render_template(
            "index.html",
            result="⚠️ ERROR",
            reason="ML processing failed",
            language=lang
        )

    # ⚠️ ADJUST BASED ON YOUR MODEL LABEL
    if prediction == 1:
        result = "❌ FAKE MESSAGE"
        reason = "ML model classified as scam"
    else:
        result = "✅ REAL MESSAGE"
        reason = "ML model classified as legitimate"

    return render_template(
        "index.html",
        result=result,
        reason=reason,
        language=lang
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
