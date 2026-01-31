# Distance Betting Platform - BiathlONE

A real-time betting platform where users bet on how close a ball will land to a target, with live odds calculation and automated credit payouts. **No wallet required!**

## Features

- 🎯 **Real-time Video Analysis**: Tracks ball and target positions using computer vision
- 💰 **Dynamic Betting System**: Live odds calculation based on bet distribution
- 🌐 **Web Interface**: Beautiful, real-time betting interface with WebSocket updates
- 💸 **Automated Payouts**: Instant credit payouts - no blockchain needed!
- 📊 **Live Statistics**: Real-time pool size, odds, and leaderboard
- 🎮 **Zero Barrier Entry**: Just pick a username and start betting (free credits included!)

## How It Works

1. **Video Analysis**: Camera detects colored target zones and tracks ball position
2. **Distance Calculation**: Measures pixel distance from ball to target center (green zone)
3. **Betting**: Users place bets predicting the final distance (just need a username!)
4. **Odds Calculation**: Dynamic odds based on bet distribution and accuracy ranges
5. **Winner Selection**: Payouts distributed proportionally based on prediction accuracy
6. **Automated Payouts**: Winners receive credits automatically (no wallet needed!)

## Installation

### Prerequisites

- Python 3.8+
- Webcam

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install opencv-python numpy flask flask-cors flask-socketio
```

## Setup

### 1. Test Camera

Make sure your camera is connected. Test with:

```bash
python video_analysis.py
```

Press 'q' to quit. Adjust color ranges if needed for your lighting.

### 2. Run the Platform

```bash
python main.py
```

Then open http://localhost:5000 in your browser.

## Running the Platform

### Basic Usage

```bash
python main.py
```

Then open http://localhost:5000 in your browser.

### Advanced Options

```bash
# Use different camera (0 for built-in, 1 for external)
python main.py --camera 0

# Use different port
python main.py --port 8080

# Run without video window (headless)
python main.py --no-video
```

## Usage Guide

### For Administrators

1. Start the application
2. Open the web interface
3. Click **"Start Game"** to begin a betting round
4. Wait for players to place bets
5. Click **"End Game"** when the ball lands
6. System automatically calculates winners and can process payouts

### For Players

1. Open the web interface (http://localhost:5000)
2. Enter any username you want
3. Choose bet amount in credits (new users automatically get 10 free credits!)
4. Predict the distance (in pixels)
5. Click **"Place Bet"**
6. Watch live odds and distance updates
7. Wait for game to end and see if you won!

## Project Structure

```
UTRA2026/
├── main.py                 # Main application entry point
├── video_analysis.py       # Computer vision for ball/target tracking
├── betting_system.py       # Betting logic and odds calculation
├── solana.py              # Payment/credit tracking system (renamed but no blockchain)
├── web_server.py          # Flask web server with WebSocket
├── templates/
│   └── index.html         # Web interface
├── requirements.txt       # Python dependencies
└── README.md
```

## Betting Odds System

The platform uses dynamic odds based on distance ranges:

| Range | Distance | Base Multiplier |
|-------|----------|----------------|
| Bullseye | 0-50px | 5.0x |
| Very Close | 51-100px | 3.0x |
| Close | 101-200px | 2.0x |
| Medium | 201-300px | 1.5x |
| Far | 301-500px | 1.2x |
| Very Far | 501+px | 1.0x |

Actual odds adjust dynamically based on:
- Total pool size
- Distribution of bets across ranges
- 5% house edge

**Note**: All amounts are in credits, not real money. Perfect for demos and testing!

## Winner Calculation

Winners are determined by **prediction accuracy**:

1. Calculate error: `|predicted_distance - actual_distance|`
2. Calculate accuracy: `1 / (1 + error)`
3. Distribute pool proportionally to accuracy
4. Bonus: Very close predictions (< 50px error) guaranteed minimum 10% profit

## Troubleshooting

### Camera Not Working

- Try different camera index: `python main.py --camera 0`
- Check camera permissions in System Preferences
- Test with: `python video_analysis.py`

### Colors Not Detected

- Adjust HSV color ranges in `video_analysis.py`
- Ensure good lighting conditions
- Use solid colored objects (green target, black ball)

### Solana Errors

- Verify private key format (should be ~88 characters, base58)
- Check wallet has sufficient balance
- Ensure using devnet RPC: `https://api.devnet.solana.com`

### Web Interface Not Loading

- Check if port 5000 is already in use
- Try different port: `python main.py --port 8080`
- Check firewall settings

## Development

### Testing Betting System

```bash
python betting_system.py
```

### Testing Video Analysis

```bash
python video_analysis.py
```

### Testing Solana Payouts

```bash
python solana.py
```

**Note**: This file has been repurposed as a simple credit tracking system - no actual blockchain integration.

## Security Notes

- **No real money involved** - all credits are for demo/testing purposes
- User data stored in memory only (cleared on restart)
- Optional: Save state to JSON file for persistence
- Perfect for hackathons, demos, and prototypes

## Why No Blockchain?

This version uses a simple credit system instead of Solana because:
- ✅ **Zero barrier to entry** - no wallet setup required
- ✅ **Instant onboarding** - pick a username and start playing
- ✅ **Perfect for demos** - no funding or transaction delays
- ✅ **Easy testing** - unlimited free credits for development
- ✅ **Hackathon friendly** - focus on the core game mechanics

Want to add real payments later? The architecture is modular - just swap the `PaymentManager` with a real payment provider!

## Future Enhancements

- [ ] User authentication system
- [ ] Historical game statistics
- [ ] Multiple game modes
- [ ] Mobile app integration
- [ ] Tournament system
- [ ] Live streaming integration
- [ ] Advanced analytics dashboard

## License

MIT License - Feel free to use for your hackathon project!

## Credits

Built for UTRA 2026 Hackathon
