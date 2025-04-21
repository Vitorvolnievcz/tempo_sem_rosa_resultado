from flask import Flask, jsonify
import json

app = Flask(__name__)

@app.route("/api/sem_vela_rosa_resultado")
def api_resultado():
    with open("data/sem_vela_rosa_resultado.json", encoding="utf-8") as f:
        return jsonify(json.load(f))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
