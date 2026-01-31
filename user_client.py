import pymongo
from datetime import datetime

# --- CONFIGURATION ---
MONGO_URI = "mongodb://localhost:27017/" # Update if using Atlas/Cloud
DB_NAME = "BiathlonBetting"

def place_bet():
    # 1. Connect to Database
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    games_col = db["games"]
    bets_col = db["bets"]

    # 2. Check for an Active Game
    # We look for a game that is 'OPEN' for betting
    active_game = games_col.find_one({"status": "OPEN"})
    
    if not active_game:
        print("\n🚫 No active games found. Please wait for the Host to start a game.")
        return

    print(f"\n--- JOINING GAME: {active_game['_id']} ---")
    print(f"Current Payout Multiplier: {active_game['payout']}x")

    # 3. User Inputs
    username = input("Enter your Username: ").strip()
    try:
        amount = float(input("Enter Bet Amount ($): "))
    except ValueError:
        print("Invalid amount.")
        return

    # Choose a target region
    print("Which Zone will the ball hit? (Green, Red, Blue)")
    choice = input("Your Choice: ").strip().upper()

    if choice not in ["GREEN", "RED", "BLUE"]:
        print("Invalid choice. Please pick Green, Red, or Blue.")
        return

    # 4. Send Bet to MongoDB
    bet_document = {
        "game_id": active_game["_id"],
        "user": username,
        "amount": amount,
        "choice": choice,
        "status": "PENDING",
        "timestamp": datetime.now()
    }

    bets_col.insert_one(bet_document)
    print(f"\n✅ Bet Placed! Good luck, {username}.")

if __name__ == "__main__":
    place_bet()