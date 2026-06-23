import os
import json
from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

def load_digest():
    try:
        with open("data/digest.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

@app.route("/")
def index():
    digest = load_digest()
    return render_template("index.html", digest=digest)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)