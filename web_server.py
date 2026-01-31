from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import pymongo
from datetime import datetime
import threading
import time
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'biathlon-betting-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- DB CONNECTION ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "BiathlonBetting"
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
games_col = db["games"]
bets_col = db["bets"]

# --- WEB ROUTES ---

@app.route('/')
def index():
    """User betting interface"""
    return render_template('index.html')

@app.route('/host')
def host():
    """Host control panel"""
    return render_template('host.html')

@app.route('/api/game/current', methods=['GET'])
def get_current_game():
    """Get the current active game"""
    game = games_col.find_one({"status": "OPEN"})
    if game:
        # Count total bets
        total_bets = bets_col.count_documents({"game_id": game["_id"]})
        return jsonify({
            "success": True,
            "game": {
                "id": game["_id"],
                "status": game["status"],
                "payout": game["payout"],
                "created_at": game["created_at"].isoformat(),
                "total_bets": total_bets
            }
        })
    return jsonify({"success": False, "message": "No active game"})

@app.route('/api/game/bets/<game_id>', methods=['GET'])
def get_game_bets(game_id):
    """Get all bets for a game"""
    bets = list(bets_col.find({"game_id": game_id}))
    # Convert ObjectId to string
    for bet in bets:
        bet['_id'] = str(bet['_id'])
        bet['timestamp'] = bet['timestamp'].isoformat() if 'timestamp' in bet else None
    return jsonify({"success": True, "bets": bets})

@app.route('/api/bet/place', methods=['POST'])
def place_bet():
    """Place a bet"""
    data = request.json
    username = data.get('username')
    amount = data.get('amount')
    choice = data.get('choice')
    
    if not username or not amount or not choice:
        return jsonify({"success": False, "message": "Missing required fields"})
    
    # Check for active game
    active_game = games_col.find_one({"status": "OPEN"})
    if not active_game:
        return jsonify({"success": False, "message": "No active game"})
    
    # Validate choice
    if choice not in ["GREEN", "RED", "BLUE"]:
        return jsonify({"success": False, "message": "Invalid choice"})
    
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({"success": False, "message": "Amount must be positive"})
    except ValueError:
        return jsonify({"success": False, "message": "Invalid amount"})
    
    # Create bet
    bet_document = {
        "game_id": active_game["_id"],
        "user": username,
        "amount": amount,
        "choice": choice,
        "status": "PENDING",
        "timestamp": datetime.now()
    }
    
    result = bets_col.insert_one(bet_document)
    
    # Notify all clients via WebSocket
    socketio.emit('bet_placed', {
        "user": username,
        "amount": amount,
        "choice": choice,
        "game_id": active_game["_id"]
    })
    
    return jsonify({
        "success": True,
        "message": f"Bet placed! Good luck, {username}!",
        "bet_id": str(result.inserted_id)
    })

@app.route('/api/game/results/<game_id>', methods=['GET'])
def get_game_results(game_id):
    """Get results for a completed game"""
    game = games_col.find_one({"_id": game_id})
    if not game:
        return jsonify({"success": False, "message": "Game not found"})
    
    bets = list(bets_col.find({"game_id": game_id}))
    for bet in bets:
        bet['_id'] = str(bet['_id'])
        bet['timestamp'] = bet['timestamp'].isoformat() if 'timestamp' in bet else None
    
    return jsonify({
        "success": True,
        "game": {
            "id": game["_id"],
            "status": game["status"],
            "winner": game.get("winner", "NONE"),
            "payout": game["payout"]
        },
        "bets": bets
    })

@app.route('/api/game/recent-completed', methods=['GET'])
def get_recent_completed():
    """Get the most recently completed game"""
    game = games_col.find_one(
        {"status": "COMPLETED"},
        sort=[("created_at", -1)]
    )
    
    if not game:
        return jsonify({"success": False, "message": "No completed games"})
    
    bets = list(bets_col.find({"game_id": game["_id"]}))
    for bet in bets:
        bet['_id'] = str(bet['_id'])
        bet['timestamp'] = bet['timestamp'].isoformat() if 'timestamp' in bet else None
    
    return jsonify({
        "success": True,
        "game": {
            "id": game["_id"],
            "status": game["status"],
            "winner": game.get("winner", "NONE"),
            "payout": game["payout"],
            "created_at": game["created_at"].isoformat()
        },
        "bets": bets
    })


@app.route('/api/game/create', methods=['POST'])
def create_game():
    """Create a new game"""
    try:
        data = request.get_json() or {}
        payout = data.get('payout', 2.0)
        
        print(f"[CREATE GAME] Received request with payout: {payout}")
        
        # Check if there's already an active game
        existing_game = games_col.find_one({"status": {"$in": ["OPEN", "LIVE"]}})
        if existing_game:
            print(f"[CREATE GAME] Game already exists: {existing_game['_id']}")
            return jsonify({"success": False, "message": "There's already an active game"})
        
        payout = float(payout)
        if payout < 1:
            return jsonify({"success": False, "message": "Payout must be at least 1.0"})
        
        game_id = str(uuid.uuid4())[:8]
        
        games_col.insert_one({
            "_id": game_id,
            "status": "OPEN",
            "payout": payout,
            "created_at": datetime.now()
        })
        
        print(f"[CREATE GAME] Game created successfully: {game_id}")
        
        # Notify all clients
        socketio.emit('game_started', {"game_id": game_id, "payout": payout})
        
        return jsonify({
            "success": True,
            "message": "Game created successfully",
            "game_id": game_id
        })
    except Exception as e:
        print(f"[CREATE GAME] Error: {str(e)}")
        return jsonify({"success": False, "message": f"Error creating game: {str(e)}"})

@app.route('/api/game/close', methods=['POST'])
def close_game():
    """Close betting for a game"""
    data = request.json
    game_id = data.get('game_id')
    
    if not game_id:
        return jsonify({"success": False, "message": "Game ID required"})
    
    result = games_col.update_one(
        {"_id": game_id, "status": "OPEN"},
        {"$set": {"status": "LIVE"}}
    )
    
    if result.modified_count > 0:
        # Notify all clients
        socketio.emit('game_closed', {"game_id": game_id})
        return jsonify({"success": True, "message": "Betting closed"})
    else:
        return jsonify({"success": False, "message": "Game not found or already closed"})


# --- WebSocket Events ---

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'message': 'Connected to betting server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    print("🌐 Starting Biathlon Betting Web Server...")
    print("👤 User Interface: http://localhost:5000")
    print("🎮 Host Interface: http://localhost:5000/host")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
