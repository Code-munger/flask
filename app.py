import requests
from flask import Flask, request, jsonify, send_from_directory
import os
import numpy as np

app = Flask(__name__)

app = Flask(__name__)
from flask import Flask
from flask_cors import CORS  # Add this line
app = Flask(__name__)
CORS(app)  # Add this line immediately after defining 'app'

# API Keys (Enter your own API keys here)
OPENWEATHER_API_KEY = '5c7b9b0cef3bf8c09d394fa64a22ee7a'
NOAA_API_KEY = 'KKKViuNUzPggYQhPLahwbAYgRyVSEdvY'

# Home Route to avoid 404 on root access
@app.route('/')
def home():
    return "Welcome to the Roof Damage Prediction App!"

# Route to serve the favicon (to avoid 404 error for favicon.ico)
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')

# Helper function to get weather data from OpenWeather
def get_weather_data(zip_code):
    url = f"http://api.openweathermap.org/data/2.5/weather?zip={zip_code},us&appid={OPENWEATHER_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        return None

# Helper function to get storm data from NOAA
def get_storm_data(zip_code):
    lat, lon = get_coordinates(zip_code)  # Convert zip code to latitude and longitude

    # NOAA storm event data API endpoint
    url = f"https://www.ncdc.noaa.gov/cdo-web/api/v2/stormevents?latitude={lat}&longitude={lon}&startDate=2020-01-01&endDate=2021-01-01"
    headers = {'Token': NOAA_API_KEY}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None

# Helper function to get coordinates from ZIP code (using OpenWeather API)
def get_coordinates(zip_code):
    weather_data = get_weather_data(zip_code)
    lat = weather_data['coord']['lat']
    lon = weather_data['coord']['lon']
    return lat, lon

# Calculate temperature risk based on the new formula
def calculate_temperature_risk(temperature):
    if temperature >= 95 or temperature <= 40:
        return 1  # Extreme heat or extreme cold
    elif 89 <= temperature < 95:
        return max(0, min(1, 0.5 + (temperature - 89) / 5))  # Moderate risk range (ensure between 0 and 1)
    else:
        return 0  # Low risk for temperatures between 40°F and 89°F

# Calculate wind speed risk based on the roof type
def calculate_wind_speed_risk(wind_speed, roof_type):
    # Classify Tile, Flat, and Wood as Asphalt for risk calculation
    if roof_type in ['tile', 'flat', 'wood']:
        roof_type = 'asphalt'  # Treat Tile, Flat, and Wood as Asphalt

    if roof_type == 'asphalt':
        min_speed = 60  # Minimum wind speed for asphalt
        max_speed = 80  # Maximum wind speed for asphalt
    elif roof_type == 'metal':
        min_speed = 0
        max_speed = 140  # Maximum wind speed for metal
    elif roof_type == 'architectural':
        min_speed = 0
        max_speed = 100  # Maximum wind speed for architectural shingles

    # Normalize wind speed to scale between 0 and 1
    if wind_speed >= max_speed:
        return 1  # High risk if wind speed exceeds max threshold
    return max(0, min(1, (wind_speed - min_speed) / (max_speed - min_speed)))  # Ensure wind risk is between 0 and 1

# Calculate rain risk based on the formula
def calculate_rain_risk(rain_weight):
    max_rain_weight = 20  # Maximum rain weight (20 pounds per square foot)
    return max(0, min(1, rain_weight / max_rain_weight))  # Cap rain risk at 1, and ensure it's not negative

# Calculate roof age risk based on the age of the roof
def calculate_roof_age_risk(roof_age):
    if roof_age <= 4:
        return 0  # Low risk (1-4 years old)
    elif 5 <= roof_age <= 7:
        # Normalize risk for ages between 5 and 7 years
        return max(0, min(1, 0.5 + (roof_age - 5) / 2))  # Risk scales between 0.5 and 1
    else:
        return 1  # High risk (8 years and older)

# Calculate the final roof damage risk considering age, weather, and storm data
def calculate_final_damage_risk(temperature, wind_speed, rain_weight, roof_age, roof_type):
    # Calculate individual risks
    temperature_risk = calculate_temperature_risk(temperature)
    wind_speed_risk = calculate_wind_speed_risk(wind_speed, roof_type)
    rain_risk = calculate_rain_risk(rain_weight)
    roof_age_risk = calculate_roof_age_risk(roof_age)
    
    # Final damage risk combines the individual risks (you can adjust the weights)
    final_damage_risk = (temperature_risk * 0.3) + (wind_speed_risk * 0.3) + (rain_risk * 0.2) + (roof_age_risk * 0.2)
    
    return max(0, min(1, final_damage_risk))  # Ensure final risk is between 0 and 1

# Route to analyze the damage risk based on user input
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    zip_code = data['zip_code']
    address = data['address']  # Address input
    roof_type = data['roof_type']
    roof_age = data['roof_age']
    
    # Fetch weather data from OpenWeather
    weather_data = get_weather_data(zip_code)
    if not weather_data:
        return jsonify({'error': 'Could not fetch weather data'}), 400
    
    # Extract relevant weather data
    temperature = weather_data['main']['temp'] - 273.15  # Convert from Kelvin to Fahrenheit
    wind_speed = weather_data['wind']['speed']
    rain_weight = weather_data.get('rain', {}).get('1h', 0)  # Get rain weight if available
    
    # Calculate the final roof damage risk
    damage_risk = calculate_final_damage_risk(temperature, wind_speed, rain_weight, roof_age, roof_type)
    
    # Return the result
    return jsonify({'damage_probability': damage_risk})

if __name__ == '__main__':
    app.run(debug=True)





