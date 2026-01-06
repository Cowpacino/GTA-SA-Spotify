    # Spotify Setup Instructions:
    # 1. Go to https://developer.spotify.com/dashboard
    # 2. Create an app and get Client ID and Client Secret
    # 3. Set redirect URI to: http://localhost:8888/callback
    # 4. Set environment variables:
    #    - SPOTIPY_CLIENT_ID=your_client_id
    #    - SPOTIPY_CLIENT_SECRET=your_client_secret
    #    - SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
    # 5. Or pass credentials directly:
    #    monitor = GTARadioMonitor(
    #        spotify_client_id="your_client_id",
    #        spotify_client_secret="your_client_secret"
    #    )