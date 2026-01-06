# GTA San Andreas Spotify Integration

Automatically sync your Spotify playback with GTA San Andreas user radio station. 

## Prerequisites

- Python 3.7 or higher
- GTA San Andreas installed
- Spotify Desktop App (for Method 1) or Spotify Premium Account (for Method 2)

## Installation

1. **Clone this repository**
```bash
   git clone https://github.com/Cowpacino/GTA-SA-Spotify
   cd GTA-SA-Spotify
```

2. **Create a virtual environment**
```bash
   python -m venv .venv
```

3. **Activate the virtual environment**
   - Windows:
```bash
     .venv\Scripts\activate
```
   - Linux/Mac:
```bash
     source .venv/bin/activate
```

4. **Install dependencies**
```bash
   pip install -r requirements.txt
```

5. **Copy audio files to GTA San Andreas**
   - Copy all files from the `asset` folder (not the folder itself) to:
```
     %USERPROFILE%\Documents\GTA San Andreas User Files\User Tracks
```
   - Example path: `C:\Users\YourName\Documents\GTA San Andreas User Files\User Tracks`

## Configuration

Choose one of the two methods below:

### Method 1: Desktop Control (Recommended for Beginners)

This method controls your Spotify desktop app directly using keyboard shortcuts.

1. **Create a `.env` file** in the project root with:
```
   SPOTIFY_METHOD=pywinauto
```

2. **Configure Spotify controls** in `config.ini` (set your Spotify hotkeys)

3. **Run the script**
```bash
   python main.py
```

---

### Method 2: Spotify API (Recommended for Advanced Users)

This method uses Spotify's Web API for more reliable control. Requires Spotify Premium.

1. **Create a Spotify Developer App**
   - Go to [https://developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
   - Click "Create App"
   - Fill in the app details
   - Set Redirect URI to: `http://localhost:8888/callback`
   - Save and copy your **Client ID** and **Client Secret**

2. **Create a `.env` file** in the project root with:
```
   SPOTIFY_METHOD=api
   SPOTIPY_CLIENT_ID=your_client_id_here
   SPOTIPY_CLIENT_SECRET=your_client_secret_here
   SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
```

3. **Run the script**
```bash
   python main.py
```
   - On first run, a browser window will open for Spotify authentication
   - Log in and authorize the app
   - You only need to do this once

## Usage

1. Launch GTA San Andreas
2. Go to Options → Audio Setup → User Track Options
3. Click "Scan User Tracks"
4. Set Play Mode to "Sequential"
5. Run the script: `python main.py`
6. Switch to user radio station in-game
7. Spotify will automatically play the corresponding playlist

## Troubleshooting

- **Method 1 not working?** Check that your Spotify hotkeys in `config.ini` match your actual Spotify settings
- **Method 2 not working?** Verify your Spotify app credentials and ensure you have Spotify Premium
- **Audio files not detected?** Make sure files are copied directly into the User Tracks folder, not in a subfolder

## Project Structure
```
.
├── asset/              # Dummy silenced Audio files for GTA radio detection
├── main.py             # Main script
├── config.ini          # Configuration file
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create this)
└── README.md          # This file
```

## Feedback and Contribution

Any Feedback is apperciated! Please open an issue or submit a pull request.