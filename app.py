from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import requests
import constants
import json
import time
from datetime import datetime
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = "Secret Key"
socketio = SocketIO(app, cors_allowed_origins="*")

class LocationManager:
    def __init__(self, json_file='static/locations.json'):
        self.json_file = json_file
        self.locations = self.load_locations()

    def load_locations(self):
        try:
            with open(self.json_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_location(self, name, lat, lon):
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("Invalid coordinates.")

        self.locations[name] = {'lat': lat, 'lon': lon}
        self.save_to_file()

    def save_to_file(self):
        with open(self.json_file, 'w') as f:
            json.dump(self.locations, f, indent=4)

    def get_location(self, name):
        return self.locations.get(name, None)


class WeatherService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://api.openweathermap.org/data/2.5/forecast'
        self.cache = {}
        self.cache_timeout = 300

    def get_weather(self, location, coords=None):
        current_time = time.time()
        if location in self.cache and (current_time - self.cache[location]['timestamp'] < self.cache_timeout):
            return self.cache[location]['data']

        params = {
            'lat': coords[0],
            'lon': coords[1],
            'appid': self.api_key,
            'units': 'metric'
        } if coords else {
            'q': location,
            'appid': self.api_key,
            'units': 'metric'
        }

        response = requests.get(self.base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            self.cache[location] = {'data': data, 'timestamp': current_time}
            return data
        return None


class RecommendationService:
    def __init__(self, weather_service, location_manager):
        self.weather_service = weather_service
        self.location_manager = location_manager

    def recommend_location(self, locations):
        sunny_count = 0
        cloudy_count = 0
        rainy_count = 0
        location_scores = {}
        location_details = {}

        for location in locations:
            loc_data = self.location_manager.get_location(location)

            if loc_data:
                coords = (loc_data['lat'], loc_data['lon'])
                weather_data = self.weather_service.get_weather(location, coords)
            else:
                weather_data = self.weather_service.get_weather(location)

            if weather_data:
                forecast = []
                processed_days = set()
                location_sunny = 0
                location_cloudy = 0
                location_rainy = 0

                for item in weather_data['list']:
                    date = item['dt_txt'].split(' ')[0]

                    if date not in processed_days and len(processed_days) < 5:
                        weather_description = item['weather'][0]['description'].lower()

                        # Categorising the weather types and counting them
                        if 'clear' in weather_description or 'sunny' in weather_description:
                            sunny_count += 1
                            location_sunny += 1
                            location_scores[location] = location_scores.get(location, 0) + 1  # Sunny = good
                        elif 'cloud' in weather_description:
                            cloudy_count += 1
                            location_cloudy += 1
                            location_scores[location] = location_scores.get(location, 0) + 0  # Cloudy = okay
                        elif 'rain' in weather_description or 'drizzle' in weather_description:
                            rainy_count += 1
                            location_rainy += 1
                            location_scores[location] = location_scores.get(location, 0) - 1  # Rainy = bad

                        processed_days.add(date)

                # Store the weather breakdown for each location
                location_details[location] = {
                    "sunny": location_sunny,
                    "cloudy": location_cloudy,
                    "rainy": location_rainy
                }

        # Making a recommendation based on the highest score
        best_location = max(location_scores, key=location_scores.get, default=None)

        if best_location:
            recommendation = f"Based on the weather forecast, I recommend {best_location.capitalize()} for your trip!"
            breakdown = "<br>Weather Breakdown for Each Location:<br>"

            for location, details in location_details.items():
                capitalised_location = location.capitalize()
                breakdown += f"<br>{capitalised_location} - Sunny: {details['sunny']} day(s), Cloudy: {details['cloudy']} day(s), Rainy: {details['rainy']} day(s)\n"

            return recommendation + breakdown
        else:
            return "Sorry, I couldn't recommend a location based on the weather data."


class WeatherBot:
    def __init__(self, api_key):
        self.location_manager = LocationManager()
        self.weather_service = WeatherService(api_key)
        self.chatbot = self.load_chatbot()
        self.recommendation_service = RecommendationService(self.weather_service, self.location_manager)

    def load_chatbot(self):
        chatbot = ChatBot('TravelBot', storage_adapter='chatterbot.storage.SQLStorageAdapter',
                          database_uri='sqlite:///travelbot.sqlite3')


        if not os.path.exists('travelbot.sqlite3'):
            trainer = ChatterBotCorpusTrainer(chatbot)
            trainer.train('chatterbot.corpus.english')
        return chatbot

    def process_message(self, message):
        if message.startswith('save '):
            return self.handle_save(message)
        elif message.startswith('weather '):
            return self.handle_weather(message)
        elif message.startswith('recommend '):
            return self.handle_recommend(message)
        else:
            return str(self.chatbot.get_response(message))

    def handle_save(self, message):
        try:
            parts = message.split()
            name = parts[1].capitalize()
            lat = float(parts[2])
            lon = float(parts[3])
            self.location_manager.save_location(name, lat, lon)
            return f"Location '{name}' saved with coordinates ({lat}, {lon})."
        except Exception as e:
            return f"Error saving location: {str(e)}"

    def handle_weather(self, message):
        location = message.split(' ', 1)[1].capitalize()
        loc_data = self.location_manager.get_location(location)

        if loc_data:
            coords = (loc_data['lat'], loc_data['lon'])
            data = self.weather_service.get_weather(location, coords)
        else:
            data = self.weather_service.get_weather(location)

        if data:
            forecast = []
            processed_days = set()

            for item in data['list']:
                date = item['dt_txt'].split(' ')[0]

                if date not in processed_days and len(processed_days) < 5:
                    weather_description = item['weather'][0]['description'].capitalize()
                    temp = item['main']['temp']
                    feels_like = item['main']['feels_like']
                    humidity = item['main']['humidity']
                    wind_speed = item['wind']['speed']

                    forecast.append(
                        f"<br>{date}: {weather_description}, Temp: {temp}°C, Feels like: {feels_like}°C, "
                        f"Humidity: {humidity}%, Wind Speed: {wind_speed} m/s."
                    )

                    processed_days.add(date)

            if forecast:
                return f"5-Day Forecast for {location}:\n" + "\n".join(forecast)
            else:
                return f"Could not retrieve a complete 5-day forecast for {location}."

        return f"Failed to retrieve weather data for {location}."

    def handle_recommend(self, message):
        locations = message.split()[1:]
        return self.recommendation_service.recommend_location(locations)


weather_bot = WeatherBot(constants.API_KEY)

@app.route('/')
def index():
    return render_template('index.html', api_key=constants.API_KEY)


@socketio.on('send_message')
def handle_message(data):
    user_message = data.get('message')
    response_message = weather_bot.process_message(user_message)
    emit('receive_message', {'message': response_message})


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=False, allow_unsafe_werkzeug=True)
