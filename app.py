from flask import Flask, request, jsonify, render_template
from plenzo_nogui import plenzo_search  # uses your existing scraper

app = Flask(__name__)


@app.route("/")
def home():
    # Renders the search UI
    return render_template("index.html")


@app.route("/api/search")
def api_search():
    """
    HTTP API endpoint:
      GET /api/search?q=camera

    Returns:
      {
        "query": "camera",
        "results": [
          {"rank": 1, "title": "...", "link": "...", "imageUrl": "..."},
          ...
        ]
      }
    """
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({"error": "Missing 'q' query parameter"}), 400

    try:
        deals = plenzo_search(query)  # calls your Selenium scraper
        return jsonify({"query": query, "results": deals})
    except Exception as e:
        # Log error to console for debugging
        print("Error in plenzo_search:", e)
        return jsonify({"error": "Search failed on the server."}), 500


if __name__ == "__main__":
    # For local dev
    app.run(host="0.0.0.0", port=5000, debug=True)
