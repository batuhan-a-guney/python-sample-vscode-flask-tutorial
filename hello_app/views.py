from datetime import datetime
import json
import os
import time
import urllib.error
import urllib.request
from flask import Flask, jsonify, render_template
from . import app

GOLD_CACHE_SECONDS = 5
GOLD_SPOT_URL = os.environ.get("GOLD_SPOT_URL", "https://api.metals.live/v1/spot")
FX_RATE_URL = os.environ.get("FX_RATE_URL", "https://open.er-api.com/v6/latest/USD")
TROY_OUNCE_IN_GRAMS = 31.1035
_gold_cache = {"fetched_at": 0, "payload": None}

def _fetch_json(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))

def _extract_gold_oz_usd(spot_payload):
    if not isinstance(spot_payload, list):
        raise ValueError("Spot verisi beklenmeyen formatta.")
    for entry in spot_payload:
        if isinstance(entry, list) and len(entry) >= 2 and entry[0] == "gold":
            return float(entry[1])
    raise ValueError("Altin spot verisi bulunamadi.")

def _extract_usd_try_rate(rate_payload):
    rates = rate_payload.get("rates", {})
    if "TRY" not in rates:
        raise ValueError("TRY kuru bulunamadi.")
    return float(rates["TRY"])

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about/")
def about():
    return render_template("about.html")

@app.route("/contact/")
def contact():
    return render_template("contact.html")

@app.route("/hello/")
@app.route("/hello/<name>")
def hello_there(name = None):
    return render_template(
        "hello_there.html",
        name=name,
        date=datetime.now()
    )

@app.route("/api/data")
def get_data():
    return app.send_static_file("data.json")

@app.route("/api/gold")
def get_gold_price():
    now = time.time()
    cached = _gold_cache.get("payload")
    if cached and now - _gold_cache["fetched_at"] < GOLD_CACHE_SECONDS:
        return jsonify(cached)

    try:
        spot_payload = _fetch_json(GOLD_SPOT_URL)
        rate_payload = _fetch_json(FX_RATE_URL)
        gold_oz_usd = _extract_gold_oz_usd(spot_payload)
        usd_try = _extract_usd_try_rate(rate_payload)
    except (urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        fallback = {
            "status": "error",
            "message": f"Altin verisi alinamadi: {exc}",
        }
        return jsonify(fallback), 502

    gram_price = (gold_oz_usd * usd_try) / TROY_OUNCE_IN_GRAMS
    result = {
        "status": "ok",
        "currency": "TRY",
        "gram_price": round(gram_price, 2),
        "updated_at": rate_payload.get("time_last_update_utc"),
    }
    _gold_cache["payload"] = result
    _gold_cache["fetched_at"] = now
    return jsonify(result)
