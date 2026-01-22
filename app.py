from flask import Flask, render_template, request
import pickle
import re
from langdetect import detect
from deep_translator import GoogleTranslator
from urllib.parse import urlparse

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

# -------- LINK ANALYSIS (GENERAL) --------
def analyze_links(text):
    urls = re.findall(r'https?://\S+|www\.\S+', text.lower())

    for url in urls:
        domain = urlparse(url if url.startswith("http") else "http://" + url).netloc

        # ❌ Known scam TLDs
        if domain.endswith((".xyz", ".top", ".online", ".site", ".link", ".click")):
            return "scam"

        # ❌ URL shortening services
        if domain.startswith(("bit.ly", "tinyurl", "t.co", "rb.gy")):
            return "scam"

        # ⚠ Unknown domain but not instant scam
        return "unknown"

    return "no_link"

# -------- LANGUAGE SCAM PATTERNS --------
TELUGU_SCAM = [
    "డబ్బు వచ్చింది", "లింక్ ఓపెన్ చేయండి",
    "మీకు కూడా వస్తుంది", "ప్రయత్నించి చూడండి"
]

HINDI_SCAM = [
    "मुझे पैसे मिले", "आपको भी मिलेगा",
    "लिंक खोलें", "अभी क्लिक करें"
]

def contains_language_scam(text, lang):
    if lang == "te":
        return any(word in text for word in TELUGU_SCAM)
    if lang == "hi":
        return any(word in text for word in HINDI_SCAM)
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

    # 2️⃣ Native language scam words
    if contains_language_scam(message, lang):
        return render_template(
            "index.html",
            result="❌ FAKE MESSAGE",
            reason="Scam keywords detected",
            language=lang
        )

    # 3️⃣ Link analysis
    link_status = analyze_links(message)

    if link_status == "scam":
        return render_template(
            "index.html",
            result="❌ FAKE MESSAGE",
            reason="Malicious or high-risk link detected",
            language=lang
        )

    # 4️⃣ Translate for ML
    message_en = translate_to_english(message) if lang != "en" else message

    # 5️⃣ ML Prediction
    data = vectorizer.transform([message_en])
    prediction = model.predict(data)[0]

    # 6️⃣ FINAL DECISION LOGIC
    if prediction == 0:
        result = "❌ FAKE MESSAGE"
        reason = "ML model classified as scam"

    elif link_status == "unknown":
        result = "⚠ POSSIBLY SUSPICIOUS"
        reason = "Unknown link detected — caution advised"

    else:
        result = "✅ REAL MESSAGE"
        reason = "No scam indicators detected"

    return render_template(
        "index.html",
        result=result,
        reason=reason,
        language=lang
    )

if __name__ == "__main__":
    app.run(debug=True)
