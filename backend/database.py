import sqlite3
from datetime import datetime, timedelta
from math import cos, radians

DB_NAME = "restaurant_cache.db"

def get_db_connection():
    """Creates a database connection."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Initializes the database and creates tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create a table to store the locations that have been scraped
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        zip_code TEXT,
        scraped_at DATETIME NOT NULL
    );
    """)

    # Create a table to store restaurant data
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS restaurants (
        id TEXT PRIMARY KEY,
        source_location_id INTEGER,
        name TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        rating REAL,
        cuisine TEXT,
        raw_data TEXT,
        FOREIGN KEY (source_location_id) REFERENCES locations (id)
    );
    """)

    # Create indexes for faster lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_locations_coords ON locations (latitude, longitude);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_restaurants_location ON restaurants (source_location_id);")

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def find_recent_location(lat, lon, max_distance_km=8, max_age_days=180):
    """
    Finds a location in the DB within a certain distance and timeframe.
    Using a simplified square box check for performance instead of haversine.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    lat_deg_per_km = 1 / 111.32
    lon_deg_per_km = 1 / (111.32 * abs(cos(radians(lat))))

    lat_margin = max_distance_km * lat_deg_per_km
    lon_margin = max_distance_km * lon_deg_per_km

    six_months_ago = datetime.now() - timedelta(days=max_age_days)

    cursor.execute("""
        SELECT * FROM locations
        WHERE latitude BETWEEN ? AND ?
          AND longitude BETWEEN ? AND ?
          AND scraped_at >= ?
        ORDER BY scraped_at DESC
        LIMIT 1
    """, (lat - lat_margin, lat + lat_margin, lon - lon_margin, lon + lon_margin, six_months_ago))

    location = cursor.fetchone()
    conn.close()
    return location

def get_restaurants_for_location(location_id):
    """Fetches all restaurants associated with a given location_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM restaurants WHERE source_location_id = ?", (location_id,))
    restaurants = cursor.fetchall()
    conn.close()
    return [dict(row) for row in restaurants]

def save_scrape_results(lat, lon, zip_code, restaurants_data):
    """Saves a new location and its associated restaurants to the DB."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Save the new location
    cursor.execute("""
        INSERT INTO locations (latitude, longitude, zip_code, scraped_at)
        VALUES (?, ?, ?, ?)
    """, (lat, lon, zip_code, datetime.now()))
    location_id = cursor.lastrowid

    # Save the restaurants
    for restaurant in restaurants_data:
        cursor.execute("""
            INSERT OR REPLACE INTO restaurants (id, source_location_id, name, latitude, longitude, rating, cuisine, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            restaurant['id'],
            location_id,
            restaurant['name'],
            restaurant.get('latitude'),
            restaurant.get('longitude'),
            restaurant.get('rating'),
            restaurant.get('cuisine'),
            str(restaurant) # Store raw data as string
        ))

    conn.commit()
    conn.close()
    return location_id


if __name__ == '__main__':
    initialize_database()
