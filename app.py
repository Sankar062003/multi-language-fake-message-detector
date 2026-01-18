from flask import Flask, render_template, request
import pickle
from googletrans import Translator

app = Flask(__name__)

model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vector.pkl", "rb"))
translator = Translator()

@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    translated = ""
    language = ""

    if request.method == "POST":
        msg = request.form["message"]

        t = translator.translate(msg, dest="en")
        translated = t.text
        language = t.src

        vec = vectorizer.transform([translated])
        pred = model.predict(vec)[0]

        if pred == "fake":
            result = "⚠ FAKE MESSAGE"
        else:
            result = "✅ NORMAL MESSAGE"

    return render_template(
        "index.html",
        result=result,
        translated=translated,
        language=language
    )

if __name__ == "__main__":
    app.run(debug=True)
