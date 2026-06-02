from flask import Flask, render_template, request
import requests
import datetime

app = Flask(__name__)

AUTHOR = "Piotr Warowny"
PORT = 3000

CITIES = {
    "Poland": {"Warsaw": {"lat": 52.2297, "lon": 21.0122}, "Krakow": {"lat": 50.0647, "lon": 19.9450}, "Lublin": {"lat": 51.2465, "lon": 22.5684}},
    "Germany": {"Berlin": {"lat": 52.5200, "lon": 13.4050}, "Munich": {"lat": 48.1351, "lon": 11.5820}},
    "USA": {"New York": {"lat": 40.7128, "lon": -74.0060}, "Los Angeles": {"lat": 34.0522, "lon": -118.2437}}
}

@app.route("/", methods=["GET", "POST"])
def index():
    weather = None
    if request.method == "POST":
        country = request.form.get("country")
        city = request.form.get("city")

        if country in CITIES and city in CITIES[country]:
            coords = CITIES[country][city]
            url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current=temperature_2m,weather_code"
            
            try:
                response = requests.get(url).json()
                if "current" in response:
                    weather = {
                        "city": city,
                        "temp": response["current"]["temperature_2m"],
                        "desc": f"Weather Code: {response['current']['weather_code']}"
                    }
            except Exception as e:
                print(f"Error fetching weather: {e}")

    return render_template("index.html", countries=CITIES, weather=weather)

if __name__ == "__main__":
    print(f"START: {datetime.datetime.now()}")
    print(f"AUTOR: {AUTHOR}")
    print(f"PORT: {PORT}")
    app.run(host="0.0.0.0", port=PORT)