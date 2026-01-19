from flask import Flask, render_template, request
import pickle

app = Flask(__name__)

# Load model & vectorizer
model = pickle.load(open("model.pkl", "rb"))
vector = pickle.load(open("vector.pkl", "rb"))

@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None
    probability = None

    if request.method == "POST":
        message = request.form["message"]

        # Vectorize message
        message_vector = vector.transform([message])

        # Prediction (0 or 1)
        pred = model.predict(message_vector)[0]

        # Probability
        prob = model.predict_proba(message_vector)[0]

        if pred == 1:
            prediction = "Fake"
            probability = round(prob[1] * 100, 2)
        else:
            prediction = "Real"
            probability = round(prob[0] * 100, 2)

    return render_template(
        "index.html",
        prediction=prediction,
        probability=probability
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

