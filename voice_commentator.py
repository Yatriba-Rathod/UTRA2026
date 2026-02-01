"""
Live Voice Commentator for Biathlon Betting using ElevenLabs
Provides quirky, happy commentary on bets as they happen!
"""

import socketio
import random
import os
import time
import tempfile
import subprocess
from elevenlabs import ElevenLabs
import google.generativeai as genai

# ElevenLabs Configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', 'sk_b0ad451dcf6305a6137583be6ea4e53cafc6f48904501569')

# Gemini Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyAlVKgY-gtbtd5DI9KuDunnsbXO-K_cHy4')

genai.configure(api_key=GEMINI_API_KEY)

# Initialize ElevenLabs client
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Initialize Gemini model (Gemma 3 27B)
gemini_model = genai.GenerativeModel('gemma-3-27b-it')

# Connect to the Socket.IO server
sio = socketio.Client()

def generate_snarky_commentary(event_type, data):
    """Generate snarky commentary using Gemini AI"""
    try:
        if event_type == 'bet_placed':
            user = data.get('user', 'Someone')
            amount = data.get('amount', 0)
            color = data.get('choice', 'unknown')
            
            prompt = f"""You are a snarky, witty sports commentator for a betting game. 
A player named '{user}' just bet ${amount:.0f} on {color}.

Generate ONE SHORT snarky comment (max 20 words) about this bet. Be playful, slightly sarcastic, but not mean.
Examples of your style:
- "Oh look, {user}'s feeling brave today with that {color} bet. Bold strategy, Cotton."
- "${amount} on {color}? Someone's either a genius or terrible with money."
- "{user} just dropped ${amount} on {color}. This should be interesting."

Your snarky comment:"""
            
        elif event_type == 'high_bet':
            amount = data.get('amount', 0)
            prompt = f"""You are a snarky sports commentator. Someone just placed a HUGE bet of ${amount:.0f}.
Generate ONE SHORT snarky reaction (max 15 words). Be impressed but sarcastic.
Your comment:"""
            
        elif event_type == 'game_started':
            payout = data.get('payout', 2.0)
            prompt = f"""You are a snarky sports commentator. A new betting game just started with a {payout}x payout multiplier.
Generate ONE SHORT snarky welcome message (max 20 words) to get people excited.
Your comment:"""
            
        elif event_type == 'betting_closed':
            prompt = """You are a snarky sports commentator. Betting just closed and the game is about to start.
Generate ONE SHORT snarky comment (max 15 words) building suspense.
Your comment:"""
        else:
            return "Let's see what happens!"
        
        response = gemini_model.generate_content(prompt)
        commentary = response.text.strip()
        
        # Clean up any quotes or extra formatting
        commentary = commentary.replace('"', '').replace('*', '').strip()
        
        return commentary
        
    except Exception as e:
        print(f"⚠️  Gemini error: {str(e)}")
        # Fallback to simple commentary
        if event_type == 'bet_placed':
            return f"{data.get('user', 'Someone')} just bet ${data.get('amount', 0):.0f} on {data.get('choice', 'a color')}!"
        return "Interesting move!"

def speak(text):
    """Convert text to speech using ElevenLabs and play it"""
    try:
        print(f"🗣️  Speaking: {text}")
        
        # Generate audio using the correct API method
        audio_generator = client.text_to_speech.convert(
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Friendly, enthusiastic voice
            text=text,
            model_id="eleven_flash_v2",
        )
        
        # Collect audio bytes from generator
        audio_bytes = b"".join(audio_generator)
        
        # Save to temporary file and play with afplay (macOS built-in)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name
        
        # Play audio using afplay (built into macOS, no dependencies!)
        subprocess.run(['afplay', temp_path], check=True)
        
        # Clean up temp file
        os.unlink(temp_path)
            
    except Exception as e:
        print(f"❌ Error speaking: {str(e)}")
        import traceback
        traceback.print_exc()

@sio.on('connect')
def on_connect():
    print("✅ Connected to betting server!")
    speak("Voice commentator is now live! Let's have some fun!")

@sio.on('disconnect')
def on_disconnect():
    print("❌ Disconnected from server")

@sio.on('bet_placed')
def on_bet_placed(data):
    """Comment on new bets"""
    user = data.get('user', 'Someone')
    amount = data.get('amount', 0)
    color = data.get('choice', 'unknown')
    
    # High bet commentary (over $100)
    if amount > 100:
        comment = generate_snarky_commentary('high_bet', {'amount': amount})
        speak(comment)
        time.sleep(0.5)
    
    # Regular bet commentary from Gemini
    comment = generate_snarky_commentary('bet_placed', data)
    speak(comment)

@sio.on('game_started')
def on_game_started(data):
    """Comment when a new game starts"""
    payout = data.get('payout', 2.0)
    comment = generate_snarky_commentary('game_started', {'payout': payout})
    speak(comment)
    time.sleep(0.5)
    speak(f"The payout is {payout}X today. Choose wisely, or don't. I'm not your financial advisor.")

@sio.on('game_closed')
def on_game_closed(data):
    """Comment when betting closes"""
    comment = generate_snarky_commentary('betting_closed', {})
    speak(comment)

def main():
    print("=" * 60)
    print("🎙️  BIATHLON BETTING VOICE COMMENTATOR")
    print("=" * 60)
    print()
    
    if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY == 'your-api-key-here':
        print("⚠️  WARNING: Please set your ElevenLabs API key!")
        print("Get your free API key at: https://elevenlabs.io/")
        print("Then set it with: export ELEVENLABS_API_KEY='your-key'")
        print()
        print("Note: Running with placeholder key - this may not work!")
        print()
    
    print("🔌 Connecting to betting server at http://localhost:5000...")
    
    try:
        sio.connect('http://localhost:5000')
        
        print("✅ Commentator is ready!")
        print("🎤 Listening for bets and game events...")
        print("Press Ctrl+C to stop")
        print()
        
        # Keep the script running
        sio.wait()
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down commentator...")
        speak("Commentator signing off! Thanks for playing!")
        sio.disconnect()
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()