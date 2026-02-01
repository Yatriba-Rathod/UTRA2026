import cv2
import numpy as np
import pymongo
import uuid
import time
import google.generativeai as genai
import os
from PIL import Image
import io

# --- CONFIGURATION ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "BiathlonBetting"

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyAlVKgY-gtbtd5DI9KuDunnsbXO-K_cHy4')
genai.configure(api_key=GEMINI_API_KEY)

# --- DB CONNECTION ---
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
games_col = db["games"]
bets_col = db["bets"]

def get_winning_color_from_camera():
    """
    Captures photo and uses Gemini API to detect which colored zone the ball is in.
    """
    cap = cv2.VideoCapture(1) # Check index (0 or 1)
    if not cap.isOpened():
        print("Error: Camera not found.")
        return "NONE"

    print("\n📸 CAMERA ON - Photo Capture Mode")
    print("👉 Press SPACEBAR to capture photo")
    print("👉 Press 'q' to quit without capturing")
    print("\n⚠️  Make sure the OpenCV window has focus (click on it)!")
    
    captured_frame = None
    photo_captured = False
    window_created = False

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️  Failed to read from camera!")
            break

        display_frame = frame.copy()
        
        if not photo_captured:
            cv2.putText(display_frame, "Press SPACEBAR to capture", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
        else:
            cv2.putText(display_frame, "Photo captured! Analyzing with AI...", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(display_frame, "Press ENTER to use this photo or 'r' to retake", (50, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow('Host View', display_frame)
        
        # Check if window was closed (only after first imshow)
        if window_created:
            try:
                if cv2.getWindowProperty('Host View', cv2.WND_PROP_VISIBLE) < 1:
                    print("⚠️  Window was closed!")
                    break
            except:
                print("⚠️  Window was closed!")
                break
        else:
            window_created = True
        
        key = cv2.waitKey(30) & 0xFF
        
        if key == ord(' '):  # Spacebar - capture photo
            captured_frame = frame.copy()
            photo_captured = True
            print("📸 Photo captured! Ready to analyze...")
            
        elif key == ord('r') and photo_captured:  # R - retake photo
            photo_captured = False
            captured_frame = None
            print("🔄 Ready to capture new photo...")
            
        elif key == 13 and photo_captured:  # Enter - analyze with Gemini
            print("🤖 Analyzing image with Gemini AI...")
            
            # Convert frame to PIL Image
            rgb_frame = cv2.cvtColor(captured_frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            
            # Analyze with Gemini
            detected_color = analyze_ball_position_with_gemini(pil_image)
            
            cap.release()
            cv2.destroyAllWindows()
            return detected_color
            
        elif key == ord('q'):  # Q - quit without saving
            print("❌ Cancelled - No photo captured")
            cap.release()
            cv2.destroyAllWindows()
            return "NONE"

    cap.release()
    cv2.destroyAllWindows()
    return "NONE"

def analyze_ball_position_with_gemini(image):
    """
    Uses Gemini API to analyze the image and determine which colored zone the ball is in.
    """
    try:
        # Initialize Gemini model (Gemma 3 27B)
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        # Craft the prompt
        prompt = """You are analyzing a biathlon betting game image with concentric colored zones and a white styrofoam ball.

The image contains 4 colored zones arranged concentrically (from outermost to innermost):
- BLUE (outermost ring)
- RED (second ring)
- GREEN (third ring)  
- BLACK (innermost/center zone)

Your task: Identify which colored zone the white styrofoam ball is currently located in.

IMPORTANT:
- Look for a white or light-colored spherical ball
- The ball will be positioned on or within one of the four colored zones
- If the ball is clearly on the boundary between two zones, choose the inner zone
- Respond with ONLY ONE WORD: either BLUE, RED, GREEN, or BLACK
- If no ball is visible or you're uncertain, respond with: NONE

Analyze the image and respond with the color name only."""
        
        # Generate response
        response = model.generate_content([prompt, image])
        
        # Extract the color from response
        result = response.text.strip().upper()
        
        # Validate response
        valid_colors = ["BLUE", "RED", "GREEN", "BLACK", "NONE"]
        if result in valid_colors:
            print(f"✅ Gemini detected: {result}")
            return result
        else:
            # Try to extract color from response
            for color in valid_colors:
                if color in result:
                    print(f"✅ Gemini detected: {color}")
                    return color
            
            print(f"⚠️  Gemini response unclear: {result}")
            print("Defaulting to: NONE")
            return "NONE"
            
    except Exception as e:
        print(f"❌ Error calling Gemini API: {str(e)}")
        print("Make sure your GEMINI_API_KEY is set correctly.")
        return "NONE"

def host_game():
    print("--- BIATHLON BETTING HOST ---")
    
    # 1. Find the active game (already created from web interface)
    active_game = games_col.find_one({"status": "LIVE"})
    
    if not active_game:
        print("❌ No LIVE game found. Please close betting from the web interface first.")
        return
    
    game_id = active_game["_id"]
    payout = active_game["payout"]
    
    print(f"\n✅ Found LIVE Game: {game_id}")
    print(f"📊 Payout Multiplier: {payout}x")
    print("\n🚀 Launching Camera...")
    
    # 4. Run Video Analysis
    winning_color = get_winning_color_from_camera()
    print(f"\n🎯 CONFIRMED RESULT: {winning_color}")
    
    # 5. Calculate Payouts
    print("\n--- CALCULATING RESULTS ---")
    
    # Find all bets for this game
    bets = list(bets_col.find({"game_id": game_id}))
    
    total_winners = 0
    total_losers = 0
    total_payouts = 0
    
    for bet in bets:
        user = bet['user']
        choice = bet['choice']
        amount = bet['amount']
        
        if choice == winning_color:
            winnings = amount * payout
            print(f"💰 {user} WON ${winnings:.2f} (Bet ${amount} on {choice})")
            bets_col.update_one({"_id": bet["_id"]}, {"$set": {"status": "WON", "winnings": winnings}})
            total_winners += 1
            total_payouts += winnings
        else:
            print(f"❌ {user} LOST (Bet ${amount} on {choice}, winner was {winning_color})")
            bets_col.update_one({"_id": bet["_id"]}, {"$set": {"status": "LOST", "winnings": 0}})
            total_losers += 1
    
    print(f"\n📊 Summary: {total_winners} Winners, {total_losers} Losers, ${total_payouts:.2f} Total Payouts")

    # Close Game
    games_col.update_one({"_id": game_id}, {"$set": {"status": "COMPLETED", "winner": winning_color}})
    print("\n✅ Game Completed.")

if __name__ == "__main__":
    from datetime import datetime
    host_game()