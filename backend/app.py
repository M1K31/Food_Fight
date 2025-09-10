import os
import random
import requests
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from apify_client import ApifyClient
from math import radians, sin, cos, sqrt, atan2
import database

# --- Initialization ---
load_dotenv()
app = Flask(__name__)
CORS(app)
database.initialize_database()

# --- API Configuration ---
GEOAPIFY_API_URL = "https://api.geoapify.com/v1/geocode/search"
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")
APIFY_API_KEY = os.getenv("APIFY_API_KEY")

# --- Helper Functions ---
def get_coords_for_zip(zip_code):
    """Geocodes a ZIP code to latitude and longitude using Geoapify."""
    if not GEOAPIFY_API_KEY or GEOAPIFY_API_KEY == "your_geoapify_api_key":
        print("WARN: Geoapify API key not found. Using mock coordinates for 90210.")
        return 34.0901, -118.4065

    params = {
        "text": zip_code, "country": "us", "format": "json", "apiKey": GEOAPIFY_API_KEY
    }
    try:
        response = requests.get(GEOAPIFY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("results"):
            loc = data["results"][0]
            return loc["lat"], loc["lon"]
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Geoapify request failed: {e}")
    return None, None

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates the distance between two lat/lon points in meters."""
    R = 6371000
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

async def get_fresh_restaurants_apify(latitude, longitude, cuisine):
    """Fetches restaurant data using the Apify Restaurant Review Aggregator actor."""
    if not APIFY_API_KEY or APIFY_API_KEY == "your_apify_api_key":
        print("WARN: Apify API key not found. Cannot fetch fresh data.")
        return []

    client = ApifyClient(APIFY_API_KEY)
    actor_id = "tri_angle/restaurant-review-aggregator"
    run_input = { "queries": f"{cuisine} restaurant", "lat": latitude, "lng": longitude, "max_reviews": 1, "max_places": 20 }

    try:
        run = await client.actor(actor_id).call(run_input)
        dataset = client.dataset(run["defaultDatasetId"])
        items_list = await dataset.list_items()
        items = items_list.items

        restaurants = []
        for item in items:
            if item.get("title") and item.get("totalScore") and item.get("location"):
                restaurants.append({
                    "id": item.get("placeId", str(random.randint(10000, 99999))),
                    "name": item["title"],
                    "latitude": item["location"]["lat"],
                    "longitude": item["location"]["lng"],
                    "rating": item.get("totalScore"),
                    "cuisine": cuisine,
                })
        return restaurants
    except Exception as e:
        print(f"ERROR: Apify actor failed: {e}")
        return []

def select_winner(restaurants):
    """Selects a winner based on rating (higher is better) and distance (lower is better)."""
    if not restaurants: return None
    for r in restaurants:
        rating_score = (r.get("rating", 0) / 5) * 10
        distance_score = max(0, (1 - (r.get("distance", 50000) / 50000))) * 10
        r["win_score"] = (rating_score * 0.7) + (distance_score * 0.3)
    restaurants.sort(key=lambda x: x.get("win_score", 0), reverse=True)
    return restaurants[0]

def generate_images(mascot1_name, mascot2_name, winner_name):
    """Generates images using Stability AI or returns placeholders."""
    if not STABILITY_API_KEY or STABILITY_API_KEY == "your_stability_api_key":
        print("WARN: Stability AI API key not found. Returning placeholder images.")
        return [
            f"https://placehold.co/512x512/EBF5FF/4A90E2?text={mascot1_name.replace(' ', '+')}\\nvs\\n{mascot2_name.replace(' ', '+')}",
            f"https://placehold.co/512x512/FFF3E0/FF9800?text=Epic+Battle!",
            f"https://placehold.co/512x512/E8F5E9/4CAF50?text={winner_name.replace(' ', '+')}\\nWins!",
        ]
    # The actual image generation logic would go here.
    # For now, we return placeholders to ensure functionality.
    return [ "https://via.placeholder.com/512.png" ] * 3

# --- Main Application Route ---
@app.route("/api/battle", methods=["POST"])
async def battle():
    data = request.get_json()
    user_lat, user_lon, zip_code = data.get("latitude"), data.get("longitude"), data.get("zip_code")
    cuisine = data.get("cuisine", "").lower()

    if not cuisine: return jsonify({"error": "Cuisine is a required field"}), 400

    if zip_code:
        lat, lon = get_coords_for_zip(zip_code)
        if not lat: return jsonify({"error": f"Could not find coordinates for ZIP code: {zip_code}"}), 404
        user_lat, user_lon = lat, lon
    elif not all([user_lat, user_lon]):
        return jsonify({"error": "Either lat/lon or a zip_code must be provided"}), 400

    try:
        restaurants = []
        cached_location = database.find_recent_location(user_lat, user_lon)
        if cached_location:
            print(f"CACHE HIT: Found recent scrape at location {cached_location['id']}")
            restaurants = database.get_restaurants_for_location(cached_location['id'])
        else:
            print("CACHE MISS: Fetching fresh data from Apify.")
            restaurants = await get_fresh_restaurants_apify(user_lat, user_lon, cuisine)
            if restaurants:
                database.save_scrape_results(user_lat, user_lon, zip_code, restaurants)

        if len(restaurants) < 2: return jsonify({"error": "Not enough restaurants found"}), 404

        for r in restaurants:
            r['distance'] = haversine_distance(user_lat, user_lon, r['latitude'], r['longitude'])

        winner = select_winner(list(restaurants))
        other_restaurants = [r for r in restaurants if r["id"] != winner["id"]]
        if not other_restaurants: return jsonify({"error": "Only one restaurant found"}), 404

        opponent = random.choice(other_restaurants)
        restaurant1, restaurant2 = winner, opponent

        mascot1_name = restaurant1["name"].split(" ")[0] + " Mascot"
        mascot2_name = opponent["name"].split(" ")[0] + " Mascot"
        winner_mascot_name = winner["name"].split(" ")[0] + " Mascot"
        images = generate_images(mascot1_name, mascot2_name, winner_mascot_name)

        return jsonify({ "restaurant1": restaurant1, "restaurant2": restaurant2, "winner": winner, "images": images })
    except Exception as e:
        print(f"An unexpected error occurred in battle route: {e}")
        return jsonify({"error": "An unexpected server error occurred"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)
