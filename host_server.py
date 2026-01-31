import cv2
import numpy as np
import pymongo
import uuid
import time

# --- CONFIGURATION ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "BiathlonBetting"

# --- DB CONNECTION ---
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
games_col = db["games"]
bets_col = db["bets"]

def get_winning_color_from_camera():
    """
    Runs the CV loop. Returns the detected color when 'q' is pressed.
    """
    cap = cv2.VideoCapture(1) # Check index (0 or 1)
    if not cap.isOpened():
        print("Error: Camera not found.")
        return "NONE"

    print("\n🎥 CAMERA ON. Press 'q' when the ball has landed to LOCK IN the result.")
    
    final_zone = "NONE"

    while True:
        ret, frame = cap.read()
        if not ret: break

        # --- COPY OF YOUR VISION LOGIC START ---
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # Masks
        mask_green = cv2.inRange(hsv, np.array([40, 70, 70]), np.array([80, 255, 255]))
        mask_blue = cv2.inRange(hsv, np.array([90, 70, 70]), np.array([130, 255, 255]))
        mask_red = cv2.inRange(hsv, np.array([0, 70, 70]), np.array([10, 255, 255])) + \
                   cv2.inRange(hsv, np.array([170, 70, 70]), np.array([180, 255, 255]))
        mask_black = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 60]))

        # Contours
        def get_largest(mask):
            cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            return max(cnts, key=cv2.contourArea) if cnts else None

        cnt_green = get_largest(mask_green)
        cnt_red = get_largest(mask_red)
        cnt_blue = get_largest(mask_blue)
        ball_contour = get_largest(mask_black)

        current_zone = "OUTSIDE"
        
        if ball_contour is not None:
            # Check Square
            peri = cv2.arcLength(ball_contour, True)
            approx = cv2.approxPolyDP(ball_contour, 0.04 * peri, True)
            
            if len(approx) == 4:
                M = cv2.moments(ball_contour)
                if M["m00"] != 0:
                    cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
                    center = (cx, cy)
                    
                    # Hierarchy Check
                    if cnt_green is not None and cv2.pointPolygonTest(cnt_green, center, False) >= 0:
                        current_zone = "GREEN"
                    elif cnt_red is not None and cv2.pointPolygonTest(cnt_red, center, False) >= 0:
                        current_zone = "RED"
                    elif cnt_blue is not None and cv2.pointPolygonTest(cnt_blue, center, False) >= 0:
                        current_zone = "BLUE"

                    # Draw
                    cv2.circle(frame, center, 5, (255, 255, 255), -1)
                    cv2.putText(frame, f"WINNER: {current_zone}", (50, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
                    
                    # Update the variable that we will return
                    final_zone = current_zone
        
        # --- VISION LOGIC END ---

        cv2.imshow('Host View', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return final_zone

def host_game():
    print("--- BIATHLON BETTING HOST ---")
    
    # 1. Setup Game Settings
    try:
        payout = float(input("Set Payout Multiplier (e.g. 2.0): "))
    except:
        payout = 2.0
        
    game_id = str(uuid.uuid4())[:8]
    
    # 2. Create Game in DB
    print(f"\nCreating Game ID: {game_id}")
    games_col.insert_one({
        "_id": game_id,
        "status": "OPEN",
        "payout": payout,
        "created_at": datetime.now()
    })
    
    print(f"✅ Game is OPEN. Waiting for users to bet...")
    input("👉 Press ENTER to CLOSE BETTING and START CAMERA...")
    
    # 3. Close Betting
    games_col.update_one({"_id": game_id}, {"$set": {"status": "LIVE"}})
    print("🚫 Betting Closed. Launching Camera...")
    
    # 4. Run Video Analysis
    winning_color = get_winning_color_from_camera()
    print(f"\n🎯 CONFIRMED RESULT: {winning_color}")
    
    # 5. Calculate Payouts
    print("\n--- CALCULATING RESULTS ---")
    
    # Find all bets for this game
    bets = bets_col.find({"game_id": game_id})
    
    for bet in bets:
        user = bet['user']
        choice = bet['choice']
        amount = bet['amount']
        
        if choice == winning_color:
            winnings = amount * payout
            print(f"💰 {user} WON ${winnings} (Bet {choice} on {winning_color})")
            bets_col.update_one({"_id": bet["_id"]}, {"$set": {"status": "WON", "winnings": winnings}})
        else:
            print(f"❌ {user} LOST (Bet {choice} on {winning_color})")
            bets_col.update_one({"_id": bet["_id"]}, {"$set": {"status": "LOST", "winnings": 0}})

    # Close Game
    games_col.update_one({"_id": game_id}, {"$set": {"status": "COMPLETED", "winner": winning_color}})
    print("\n✅ Game Completed.")

if __name__ == "__main__":
    from datetime import datetime
    host_game()