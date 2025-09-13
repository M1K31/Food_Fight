# What's for Dinner? - The Ultimate Showdown

This web application helps you decide what to have for dinner by pitting two restaurant mascots against each other in a glorious, AI-generated battle!

## How It Works

The application uses a combination of web scraping, a local database cache, and AI image generation to create a unique experience:

1.  **Location Input**: The user provides their location, either by entering a US zip code or by allowing the browser to use their current location (geolocation).
2.  **Data Fetching & Caching**:
    *   The backend first checks a local **SQLite database** to see if it has recently scraped restaurant data for the user's area.
    *   **Cache Hit**: If fresh (less than 6 months old) data is found, it's used immediately.
    *   **Cache Miss**: If no fresh data exists, the backend uses the **Apify API** to scrape data from services like Google Maps to get a list of nearby restaurants, including their user ratings. This new data is then saved to the local database for future requests.
3.  **The Battle**:
    *   The application determines the "best" restaurant from the list based on a weighted score of its **rating** (higher is better) and **distance** (closer is better).
    *   This winning restaurant is then pitted against a randomly selected opponent from the same list.
4.  **AI Image Generation**:
    *   The names of the two battling restaurants are used to generate prompts.
    *   The **Stability AI API** is called to create three images depicting the battle: a pre-battle face-off, the mid-battle action, and a victory scene for the winning mascot.
5.  **Display**: The frontend displays the three images in a sequence, along with the name and details of the champion restaurant.

## Getting Started

Follow these steps to get the application running on your local machine.

### 1. Prerequisites
- Python 3.x
- pip (Python package installer)

### 2. Installation & Setup

First, clone the repository to your local machine:
```bash
git clone <repository-url>
cd <repository-directory>
```

Next, set up the backend:
```bash
# Navigate to the backend directory
cd backend

# Install the required Python packages
pip install -r requirements.txt

# Create your personal environment file from the example
cp .env.example .env
```

Finally, you need to add your API keys to the newly created `.env` file. Open `backend/.env` in a text editor and paste your keys. The comments in the file show you where to get each key.

> **Note:** The application has fallbacks. If API keys are not provided, it will use mock data for geocoding and placeholder images, but it will not be able to fetch new restaurant data.

### 3. Running the Application

You need to run two servers simultaneously in two separate terminal windows.

**Terminal 1: Start the Backend Server**
```bash
# Make sure you are in the `backend` directory
python app.py
```
This will start the Flask server on `http://localhost:5001`. You should see output indicating the server is running.

**Terminal 2: Start the Frontend Server**
```bash
# Make sure you are in the root directory of the project
python -m http.server 8000
```
This will start a simple server for the HTML, CSS, and JS files on `http://localhost:8000`.

### 4. Access the App

Once both servers are running, open your web browser and navigate to:
**[http://localhost:8000](http://localhost:8000)**

## Uninstallation

To uninstall the application, simply delete the project directory.

To remove the installed Python packages, you can run the following command from the `backend` directory:
```bash
pip uninstall -r requirements.txt -y
```
