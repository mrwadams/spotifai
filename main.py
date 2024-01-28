import streamlit as st
from openai import OpenAI
import requests
import regex as re

def get_song_recommendations(api_key, song_details):
    """Get song recommendations based on the provided list of songs."""
    
    # Constructing the prompt
    prompt = ("I have a playlist of songs here that the user really likes. The user is open to exploring similar songs or artists. "
              "Could you suggest some tracks that have a similar vibe or feel? Here's the playlist:\n\n")

    # Listing the songs
    for song in song_details:
        prompt += f"- {song['Title']} by {song['Artist']}\n"

    # Requesting recommendations
    prompt += "\nBased on these songs, what other tracks would you recommend for someone who loves these kinds of music?"

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Sending the request to OpenAI
    completion = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    content = completion.choices[0].message.content
    return content

def extract_playlist_id(spotify_url):
    """Extracts the playlist ID from a Spotify sharing link."""
    match = re.search(r"open\.spotify\.com/playlist/(\w+)", spotify_url)
    if match:
        return match.group(1)
    else:
        st.error("Invalid Spotify playlist URL")
        return None

def request_spotify_access_token(client_id, client_secret):
    """Request an access token from Spotify."""
    url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        st.error("Failed to get access token")
        return None

def get_spotify_playlist(access_token, playlist_id):
    """Fetch a Spotify playlist and return artist and song titles."""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        playlist_data = response.json()
        song_details = []

        for track in playlist_data['tracks']['items']:
            title = track['track']['name']
            artists = ', '.join(artist['name'] for artist in track['track']['artists'])
            song_details.append({'Title': title, 'Artist': artists})

        return song_details
    else:
        st.error("Failed to get playlist")
        return None

def main():
    st.title("SpotifAI")
    st.subheader("Discover new songs with Spotify and OpenAI")

    # Sidebar for input fields with session state
    st.sidebar.title("Configuration")
    # Instructions for Spotify Credentials
    with st.sidebar.expander("How to get a Spotify Client ID and Secret"):
        st.write("""
            To get your Spotify Client ID and Secret, you need to create an app in the Spotify Developer Dashboard. Here are the steps:
            1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
            2. Log in with your Spotify account (or create one if you don't have it).
            3. Once logged in, click on 'CREATE AN APP'.
            4. Fill in the app details and agree to the terms.
            5. After the app is created, you'll see the Client ID. Click 'SHOW CLIENT SECRET' to see the secret.
            6. Use these credentials in the fields below.
        """)
    st.sidebar.text_input("Spotify Client ID", key='spotify_client_id', type='password', help="Enter your Spotify Client ID here.")
    st.sidebar.text_input("Spotify Client Secret", key='spotify_client_secret', type='password', help="Enter your Spotify Client Secret here.")
    st.sidebar.text_input("OpenAI API Key", key='openai_api_key', type='password', help="Enter your OpenAI API Key here.")
    st.sidebar.markdown("Created by [Matt Adams](https://www.linkedin.com/in/matthewrwadams/).")

    # Instructions for obtaining Spotify playlist link
    with st.expander("How to get a Spotify Playlist Link"):
        st.write("""
            To copy a Spotify playlist link:
            1. Open Spotify in your web browser and navigate to the playlist you want to share.
            2. Click the three dots (`...`) to open the playlist options.
            3. Select 'Share' and then choose 'Copy Link to Playlist'.
            4. Paste the copied link in the field below.
        """)

    # Spotify Playlist Link Input
    playlist_link = st.text_input("Spotify Playlist Link", help="Paste the Spotify playlist link here.")

    if st.button("Fetch Playlist"):
        with st.spinner("Fetching playlist..."):
            if st.session_state.spotify_client_id and st.session_state.spotify_client_secret:
                playlist_id = extract_playlist_id(playlist_link)
                if playlist_id:
                    access_token = request_spotify_access_token(
                        st.session_state.spotify_client_id, 
                        st.session_state.spotify_client_secret
                    )
                    if access_token:
                        song_details = get_spotify_playlist(access_token, playlist_id)
                        if song_details:
                            with st.expander("Show Playlist"):
                                st.table(song_details)
                            st.session_state.song_details = song_details  # Store the song details in session state
            else:
                st.error("Please enter Spotify Client ID and Secret")

    if 'song_details' in st.session_state and st.session_state.song_details:
        if st.button("Get Recommendations"):
            with st.spinner("Getting recommendations..."):
                if st.session_state.openai_api_key:
                    recommendations = get_song_recommendations(st.session_state.openai_api_key, st.session_state.song_details)
                    st.write("Recommended songs based on your playlist:")
                    st.write(recommendations)
                else:
                    st.error("Please enter OpenAI API Key")

if __name__ == "__main__":
    main()