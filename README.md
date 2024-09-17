# ADIFY AI - Spotify Playlist Generator

![ADIFY AI Logo](assets/logo.png)

**Website**: [ADIFY AI](http://adify.pro/)

ADIFY AI is a Spotify playlist generator that creates playlists based on user prompts. The system uses the Annoy index and embeddings to recommend personalized songs, making it easy to generate mood-based playlists on the fly. By entering a description of the desired playlist (e.g., "chill rock music for studying"), ADIFY AI intelligently selects songs and playlists from Spotify’s vast library that best match the user's mood or activity.

## Features
- **AI-Powered Playlist Creation**: Generates customized Spotify playlists based on a user's prompt.
- **Spotify Integration**: Automatically creates public playlists on your Spotify account and adds recommended tracks.
- **Efficient Recommendations**: Uses the Annoy index and Sentence Transformers for quick, memory-efficient song recommendations.
- **Memory Optimization**: Loads song embeddings and track info using memory-mapped files to handle large datasets efficiently.
- **Playlists**: Generates two separate playlists to reduce memory load while providing multiple options.

## How It Works
1. **User Prompt**: The user provides a text prompt describing the desired playlist.
2. **Song Recommendation**: ADIFY AI encodes the prompt using a Sentence Transformer model and finds similar song embeddings using an Annoy index.
3. **Playlist Generation**: Selected tracks are added to a newly created Spotify playlist, which is then returned to the user.
4. **Automatic Playlist Creation**: ADIFY AI creates the playlist on Spotify, including the recommended songs, and provides the user with a direct link to the playlist.

## Technology Stack
- **Flask**: Web framework for handling requests and rendering the user interface.
- **Annoy**: Efficient nearest neighbors search to quickly find similar songs.
- **Sentence Transformers**: Model for encoding user prompts into vector space.
- **Spotipy**: Python library for interacting with the Spotify API.
- **NumPy**: Handles large embeddings and song metadata efficiently.
- **Gunicorn**: Web server for running the Flask app.
- **ngrok**: Enables local development with a secure public URL.

## Try It Now
Visit [ADIFY AI](http://adify.pro/) to generate your personalized playlist!
