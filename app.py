# requirements: pip install serpapi python-dotenv openai
import os
import csv
from serpapi import GoogleSearch  # ✅ Fixed import
import openai
from dotenv import load_dotenv

# Load API keys
load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

def fetch_groceries(lat, lon, radius=1500):
    params = {
        "engine": "google_maps",
        "q": "grocery store",
        "type": "search",
        "ll": f"@{lat},{lon},15z",
        "radius": radius,
        "api_key": SERPAPI_KEY
    }
    client = GoogleSearch(params)
    return client.get_dict().get("local_results", [])

def fetch_reviews(place_id, next_page_token=None):
    params = {
        "engine": "google_maps_reviews",
        "type": "search",
        "place_id": place_id,
        "api_key": SERPAPI_KEY
    }
    if next_page_token:
        params["next_page_token"] = next_page_token
    return GoogleSearch(params).get_dict()

def summarize_review_text(review_text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": f"Summarize this review in one sentence:\n\n{review_text}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

def main():
    lat, lon = 28.4595, 77.0266  # Location: Gurugram
    groceries = fetch_groceries(lat, lon)
    
    with open("groceries.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Category", "Lat", "Lng", "Review", "ReviewDate", "ReviewSummary"])

        for g in groceries:
            pid = g.get("place_id")
            if not pid:
                continue

            next_page = None
            while True:
                rev_data = fetch_reviews(pid, next_page)
                reviews = rev_data.get("reviews", [])

                for rv in reviews:
                    review_text = rv.get("snippet", "")
                    summary = summarize_review_text(review_text) if review_text else "No review"

                    writer.writerow([
                        g.get("title", "N/A"),
                        g.get("type", "N/A"),
                        g.get("gps_coordinates", {}).get("latitude"),
                        g.get("gps_coordinates", {}).get("longitude"),
                        review_text,
                        rv.get("date", "N/A"),
                        summary
                    ])

                next_page = rev_data.get("next_page_token")
                if not next_page:
                    break

if __name__ == "__main__":
    main()
