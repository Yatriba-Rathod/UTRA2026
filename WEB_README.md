# Biathlon Betting - Web Frontend

Simple web interface for the Biathlon Betting game.

## Setup

1. **Make sure MongoDB is running:**
   ```bash
   mongod --dbpath ~/data/db
   ```

2. **Start the web server:**
   ```bash
   python web_server.py
   ```

3. **Open in your browser:**
   - **Users**: http://localhost:5000
   - **Host**: http://localhost:5000/host

## How to Use

### For Players (Users):

1. Open http://localhost:5000 in your browser
2. Enter your username
3. Enter bet amount
4. Click on a color (Green, Red, or Blue)
5. Click "Place Bet"
6. See your bet appear in the live bets list

### For Hosts:

1. Open http://localhost:5000/host in your browser
2. Set payout multiplier (e.g., 2.0)
3. Click "Start New Game"
4. Wait for players to place bets
5. When ready, click "Close Betting & Start Camera"
6. Open a new terminal and run:
   ```bash
   python host_server.py
   ```
7. The camera will open - position it to see the target and ball
8. Press 'q' when the ball has landed
9. Results will be calculated automatically

## Architecture

- **web_server.py**: Flask backend serving the web interface
- **templates/index.html**: User betting interface
- **templates/host.html**: Host control panel
- **host_server.py**: Camera integration and result processing (run separately)
- **MongoDB**: Stores games and bets

## API Endpoints

- `GET /api/game/current` - Get current active game
- `POST /api/bet/place` - Place a bet
- `POST /api/game/create` - Create a new game (host)
- `POST /api/game/close` - Close betting (host)
- `GET /api/game/bets/<game_id>` - Get all bets for a game
- `GET /api/game/results/<game_id>` - Get results for a completed game

## Real-time Updates

Uses WebSocket (Socket.IO) for:
- Live bet notifications
- Game status updates
- Real-time betting pool statistics
