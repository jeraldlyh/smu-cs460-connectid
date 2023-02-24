import os

from routes import app


@app.route("/healthcheck")
def hello():
    return "I'm alive"


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(threaded=True, host="0.0.0.0", port=port)
