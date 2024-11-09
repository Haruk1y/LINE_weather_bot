import os
import json
from datetime import datetime
from linebot import LineBotApi
from linebot.models import TextSendMessage
import requests
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-pro')

def get_weather_info():
    """Get weather information from weather API"""
    url = "https://weather.tsukumijima.net/api/forecast/city/130010"
    payload = {"city": "130010"}
    try:
        response = requests.get(url, params=payload)
        response.raise_for_status()
        tenki_data = response.json()
        
        forecast = tenki_data["forecasts"][0]
        weather_info = {
            "date": forecast["date"],
            "weather": forecast["telop"],
            "max_temp": forecast.get("temperature", {}).get("max", {}).get("celsius", "N/A"),
            "min_temp": forecast.get("temperature", {}).get("min", {}).get("celsius", "N/A"),
            "rain_probability": forecast["chanceOfRain"]["T12_18"],
            "wave": forecast["detail"]["wave"]
        }
        return weather_info
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

def get_clothing_advice(weather_info):
    """Get clothing advice from Gemini API based on weather"""
    prompt = f"""
    今日の天気情報は以下の通りです：
    - 天気: {weather_info['weather']}
    - 最高気温: {weather_info['max_temp']}°C
    - 最低気温: {weather_info['min_temp']}°C
    - 降水確率: {weather_info['rain_probability']}
    
    この天気に適した服装のアドバイスと、傘が必要かどうかを3行程度で教えてください。
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error getting clothing advice: {e}")
        return "アドバイスを取得できませんでした。"

def send_line_message():
    """Send weather information and clothing advice via LINE"""
    line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
    
    # Get weather information
    weather_info = get_weather_info()
    if not weather_info:
        return
    
    # Get clothing advice
    advice = get_clothing_advice(weather_info)
    
    # Create message
    message = f"""今日の天気をお知らせします。
日付: {weather_info['date']}
天気: {weather_info['weather']}
最高気温: {weather_info['max_temp']}°C
最低気温: {weather_info['min_temp']}°C
降水確率: {weather_info['rain_probability']}
波の高さ: {weather_info['wave']}

[服装アドバイス]
{advice}"""
    
    try:
        messages = TextSendMessage(text=message)
        line_bot_api.broadcast(messages=messages)
    except Exception as e:
        print(f"Error sending LINE message: {e}")

if __name__ == "__main__":
    send_line_message()