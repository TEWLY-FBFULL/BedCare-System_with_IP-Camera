import os
import uuid
from gtts import gTTS
from pydub import AudioSegment
import requests

class TelegramVoiceService:
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    MY_CHAT_ID = os.getenv("MY_TELEGRAM_CHAT_ID")
    
    @staticmethod
    def simulate_call(message_text: str):
        temp_mp3 = f"temp_{uuid.uuid4().hex}.mp3"
        voice_ogg = f"voice_{uuid.uuid4().hex}.ogg"

        if not TelegramVoiceService.BOT_TOKEN or not TelegramVoiceService.MY_CHAT_ID:
            print("DEBUG: Missing Telegram Config (Token or Chat ID)")
            return

        try:
            tts = gTTS(text=message_text, lang='th')
            tts.save(temp_mp3)

            audio = AudioSegment.from_mp3(temp_mp3)
            audio.export(voice_ogg, format="ogg", codec="libopus")
            url = f"https://api.telegram.org/bot{TelegramVoiceService.BOT_TOKEN}/sendVoice"
            
            with open(voice_ogg, 'rb') as v_file:
                payload = {'chat_id': TelegramVoiceService.MY_CHAT_ID, 'caption': '🚨 แจ้งเหตุฉุกเฉิน'}
                files = {'voice': v_file} 
                response = requests.post(url, data=payload, files=files)
                if response.status_code != 200:
                    print(f"DEBUG: Telegram API Error: {response.text}")
                else:
                    print(f"DEBUG: Telegram Sent Success: {message_text}")
        except Exception as e:
            print(f"DEBUG: Telegram Voice Error: {e}")
        finally:
            for f in [temp_mp3, voice_ogg]:
                if os.path.exists(f):
                    os.remove(f)