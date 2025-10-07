from flask import Flask, render_template, request, jsonify
import json, subprocess, os, time

app = Flask(__name__)

DATA_PATH = "data/search_result.json"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    if not query:
        return jsonify({"error": "No query"}), 400
    # Run scraper
    subprocess.run(["python", "search_scraper_pro.py", query], check=False)
    if not os.path.exists(DATA_PATH):
        return jsonify({"error": "No result"}), 404
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        movie = json.load(f)
    return jsonify(movie)

# ✅ New route: get latest data (for auto refresh)
@app.route('/api/latest')
def latest():
    if not os.path.exists(DATA_PATH):
        return jsonify({"error": "No data yet"}), 404
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
