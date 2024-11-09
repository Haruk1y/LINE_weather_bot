import os
import json
from datetime import datetime
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging import TextMessage, BroadcastRequest
import requests
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-pro')

def get_weather_info(city=130010):
    """Get weather information from weather API"""
    url = f"https://weather.tsukumijima.net/api/forecast?city={city}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        tenki_data = response.json()
        
        title = tenki_data["title"]
        description = tenki_data["description"]
        forecast = tenki_data["forecasts"][0]
        date_str = forecast["date"]
        
        # 降水確率の時間帯とその確率をディクショナリで保持
        rain_probs = {
            "00-06時": forecast["chanceOfRain"]["T00_06"].rstrip('%'),
            "06-12時": forecast["chanceOfRain"]["T06_12"].rstrip('%'),
            "12-18時": forecast["chanceOfRain"]["T12_18"].rstrip('%'),
            "18-24時": forecast["chanceOfRain"]["T18_24"].rstrip('%')
        }
        
        # 最大の降水確率とその時間帯を取得
        max_prob = 0
        max_time = ""
        for time, prob in rain_probs.items():
            prob_value = int(prob) if prob != '-' else 0
            if prob_value > max_prob:
                max_prob = prob_value
                max_time = time
        
        weather_info = {
            "date": datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y年%m月%d日"),
            "title": title,
            "weather": forecast["telop"],
            "max_temp": forecast["temperature"]["max"]["celsius"],
            "min_temp": forecast["temperature"]["min"]["celsius"],
            "rain_probability": max_prob,
            "rain_time": max_time
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
    - 最も降水確率が高い時間帯: {weather_info['rain_time']}
    - その時間帯の降水確率: {weather_info['rain_probability']}%
    
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
    # LINE API設定
    configuration = Configuration(
        access_token=os.environ['LINE_CHANNEL_ACCESS_TOKEN']
    )
    
    # Get weather information
    weather_info = get_weather_info()
    if not weather_info:
        return
    
    # Get clothing advice
    advice = get_clothing_advice(weather_info)
    
    # Create message
    message_text = f"""{weather_info['date']}の{weather_info['title']}をお知らせします。
天気: {weather_info['weather']}
最高気温: {weather_info['max_temp']}°C
最低気温: {weather_info['min_temp']}°C
最大降水確率: {weather_info['rain_time']}に{weather_info['rain_probability']}%

[服装アドバイス]
{advice}"""
    
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            broadcast_request = BroadcastRequest(
                messages=[
                    TextMessage(
                        type="text",
                        text=message_text
                    )
                ]
            )
            response = line_bot_api.broadcast(broadcast_request=broadcast_request)
            print("Message sent successfully")
    except Exception as e:
        print(f"Error sending LINE message: {e}")
        import traceback
        traceback.print_exc()

def verify_line_token():
    """Verify LINE Channel Access Token"""
    configuration = Configuration(
        access_token=os.environ['LINE_CHANNEL_ACCESS_TOKEN']
    )
    
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            # Get bot info to verify token
            response = line_bot_api.get_bot_info()
            print("LINE Bot verification successful")
            print(f"Bot name: {response.display_name}")
            return True
    except Exception as e:
        print(f"LINE Bot verification failed: {e}")
        return False

if __name__ == "__main__":
    # First verify the token
    if verify_line_token():
        send_line_message()
    else:
        print("Skipping message send due to token verification failure")