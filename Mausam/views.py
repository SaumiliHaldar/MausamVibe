from django.shortcuts import render
from django.conf import settings
from django.contrib import messages
import requests
import datetime, time

# Create your views here.
def index(request):
    # Fetch city name safely, default to Kolkata
    city = request.POST.get("city", request.GET.get("city", "Kolkata"))

    # Fetch API keys safely
    WEATHER_API_KEY = settings.WEATHER_API_KEY
    GOOGLE_API_KEY = settings.GOOGLE_API_KEY
    SEARCH_ENGINE_ID = settings.SEARCH_ENGINE_ID

    # Validate API keys
    if not WEATHER_API_KEY:
        return render(request, "index.html", {"error": "Weather API key is missing in settings."})
    
    if not GOOGLE_API_KEY or not SEARCH_ENGINE_ID:
        city_image_url = None  # Fallback if image API fails
    else:
        # Google Custom Search API for fetching city images
        query = f"{city} 1920x1080 {int(time.time())}"
        search_type = "image"
        city_url = (
            f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}&searchType=image"
        )

        try:
            image_response = requests.get(city_url)
            image_response.raise_for_status()
            image_data = image_response.json()

            # Extract the first image URL, fallback if empty
            city_image_url = image_data.get("items", [{}])[0].get("link", None)

        except (requests.exceptions.RequestException, IndexError, KeyError):
            city_image_url = None  # Set fallback value

    # OpenWeather API URL
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"

    try:
        # Fetch weather data
        response = requests.get(weather_url)
        response.raise_for_status()
        data = response.json()

        # Convert wind degrees to compass direction
        def wind_direction(degrees):
            directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]
            return directions[round(degrees / 45) % 8]

        weather_data = {
            "city": city,
            "description": data["weather"][0]["description"].capitalize(),
            "main_weather": data["weather"][0]["main"],  # Main condition
            "icon": data["weather"][0]["icon"],
            "temp": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": data["wind"]["speed"],
            "wind_direction": wind_direction(data["wind"]["deg"]),
            "wind_gust": data["wind"].get("gust", "N/A"),  # Gusts may not always be available
            "cloudiness": data["clouds"]["all"],  # Cloud cover %
            "visibility": data["visibility"] // 1000,  # Convert meters to kilometers
            "day": datetime.date.today(),
            "time": datetime.datetime.now().strftime("%I:%M %p"),
            "sunrise": datetime.datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%I:%M %p"),
            "sunset": datetime.datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%I:%M %p"),
            "city_image": city_image_url,  # Fetched city image URL
        }

    except requests.exceptions.RequestException:
        messages.error(request, "The city data could not be fetched. Please enter a valid city name.")
        return render(request, "index.html", {"city": city})

    return render(request, "index.html", weather_data)
