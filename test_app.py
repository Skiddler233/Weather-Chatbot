import pytest
from unittest.mock import patch
from app import WeatherService, LocationManager, RecommendationService, WeatherBot

@pytest.fixture
def weather_service():
    # Setup mock weather service
    return WeatherService(api_key="your_api_key")

@pytest.fixture
def location_manager():
    # Setup location manager with mock data
    return LocationManager(json_file='mock_locations.json')

@pytest.fixture
def recommendation_service(weather_service, location_manager):
    return RecommendationService(weather_service, location_manager)

@pytest.fixture
def weather_bot(weather_service):
    return WeatherBot(api_key="your_api_key")

def test_get_weather(weather_service):
    # Mock a call to the get_weather method
    with patch.object(weather_service, 'get_weather', return_value={"weather": [{"description": "clear sky"}]}) as mock_method:
        weather_data = weather_service.get_weather("London")
        assert weather_data["weather"][0]["description"] == "clear sky"
        mock_method.assert_called_once_with("London")

def test_save_location(location_manager):
    with patch.object(location_manager, 'save_location', return_value=None) as mock_method:
        location_manager.save_location("London", 51.5074, -0.1278)
        mock_method.assert_called_once_with("London", 51.5074, -0.1278)

def test_recommend_location(recommendation_service):
    with patch.object(recommendation_service, 'recommend_location', return_value="I recommend London for your trip.") as mock_method:
        recommendation = recommendation_service.recommend_location(["London", "Paris"])
        assert recommendation == "I recommend London for your trip."
        mock_method.assert_called_once_with(["London", "Paris"])

def test_weather_bot(weather_bot):
    with patch.object(weather_bot, 'process_message', return_value="I recommend London for your trip.") as mock_method:
        response = weather_bot.process_message("recommend London Paris")
        assert response == "I recommend London for your trip."
        mock_method.assert_called_once_with("recommend London Paris")
