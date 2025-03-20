from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import requests
import constants
import json
import time
from datetime import datetime
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

API_KEY = constants.API_KEY
BASE_URL = 'https://api.openweathermap.org/data/2.5/forecast'
CACHE = {}
CACHE_TIMEOUT = 300  # 5 minutes

# Initialize ChatterBot
chatbot = ChatBot('TravelBot')
trainer = ChatterBotCorpusTrainer(chatbot)
trainer.train('chatterbot.corpus.english')


def get_weather(location):
    current_time = time.time()

    # Check if data is cached
    if location in CACHE and (current_time - CACHE[location]['timestamp'] < CACHE_TIMEOUT):
        return CACHE[location]['data']

    # Load predefined locations
    with open('static/locations.json') as f:
        locations = json.load(f)

    if location in locations:
        # If location is found in the JSON file, use coordinates
        lat = locations[location]['lat']
        lon = locations[location]['lon']
        params = {
            'lat': lat,
            'lon': lon,
            'appid': API_KEY,
            'units': 'metric'
        }
    else:
        # Otherwise, proceed with searching by name
        params = {
            'q': location,
            'appid': API_KEY,
            'units': 'metric'
        }

    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()

        # Cache the data
        CACHE[location] = {
            'data': data,
            'timestamp': current_time
        }

        return data
    else:
        return None


def process_weather_data(data):
    forecasts = {}

    for item in data['list']:
        date_str = item['dt_txt'].split(' ')[0]
        if date_str not in forecasts:
            forecasts[date_str] = []
        forecasts[date_str].append(item)

    summary = []
    for date, weather_list in forecasts.items():
        temp_list = [entry['main']['temp'] for entry in weather_list]
        weather_descriptions = [entry['weather'][0]['description'] for entry in weather_list]
        most_common_weather = max(set(weather_descriptions), key=weather_descriptions.count)
        avg_temp = sum(temp_list) / len(temp_list)

        summary.append({
            'date': date,
            'avg_temp': round(avg_temp, 2),
            'description': most_common_weather
        })

    return summary


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('send_message')
def handle_message(data):
    user_message = data.get('message').lower()

    if not user_message:
        emit('receive_message', {'error': 'Please enter a message.'})
        return

    # Check if the message is about weather
    if 'weather' in user_message:
        if 'in' in user_message:
            location = user_message.split('in')[-1].strip()
        else:
            words = user_message.split()
            location = ' '.join(words[1:]).strip()  # Capture location after 'weather'
            if not location:
                location = 'London'  # Default location if not specified

        weather_data = get_weather(location)

        if not weather_data:
            emit('receive_message', {'error': f'Unable to retrieve weather data for {location}.'})
            return

        weather_summary = process_weather_data(weather_data)
        response_message = f"Weather forecast for {location}:<br>"

        for day in weather_summary:
            response_message += f"{day['date']}: {day['description']}, {day['avg_temp']}°C<br>"
        response_message += "<br>Hope this helps!"

    else:
        # Otherwise, use ChatterBot for general conversation
        response_message = str(chatbot.get_response(user_message))

    emit('receive_message', {'message': response_message})


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
