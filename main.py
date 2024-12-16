from datetime import datetime
from bs4 import BeautifulSoup
import requests
import spotipy
import os

client_id = os.environ['CLIENT_ID']
client_secret = os.environ["CLIENT_SECRET"]


# getting user input
user_date = input("What year do you want your playlist to be based on? (YYYY-MM-DD): ")

# validating user input
try:
    valid_date = datetime.strptime(user_date, "%Y-%m-%d")
except ValueError:
    print("Invalid date/invalid format")
    quit()

song_year = user_date.split("-")[0]


# scraping the BillBoard and getting the top 100 songs and artists
header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0"}
url = "https://www.billboard.com/charts/hot-100/" + user_date

response = requests.get(url=url, headers=header)
top_100 = response.text

soup = BeautifulSoup(top_100, "html.parser")

song_tags = soup.select("li ul li h3")
song_artist_tags = soup.select("li ul li .c-label.a-no-trucate")

song_titles = [tag.getText().strip() for tag in song_tags]
song_artists = [artist.getText().strip() for artist in song_artist_tags]


# making Spotpy object
sp = spotipy.Spotify(
    auth_manager=spotipy.SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://example.com",
        scope="playlist-modify-private",
        cache_path=".cache",
        show_dialog=True
    ))

current_user = sp.current_user()
current_user_id = current_user["id"]

# creating a playlist for the user
playlist = sp.user_playlist_create(
    user=current_user_id,
    name=f"{user_date} Top 100 Songs",
    public=False,
    description=f"Top hundred songs from the year {song_year}"
)
playlist_id = playlist["id"]


# searching for each song, and then getting its track
# if song not on Spotify, print skipped
track_uri = []
songs_num = 0
for song_name, song_artist in zip(song_titles, song_artists):
    try:
        result = sp.search(q=f"artist: {song_artist} track: {song_name} year: {song_year}", type="track", limit=1)
    except IndexError:
        print(f"{song_name} by {song_artist} not found on Spotify --> skipped.")
        continue

    # extra check in case wrong song was found
    current_song_name = result["tracks"]["items"][0]["name"]
    current_song_artist = result["tracks"]["items"][0]["artists"][0]["name"]

    if (current_song_name.strip().lower() != song_name.strip().lower()
            or current_song_artist.strip().lower() != song_artist.strip().lower()):
        print(f"Wanted: {song_name} by {song_artist}")
        print(f"Found:  {current_song_name} by {current_song_artist}")
        print("------------------")
        continue

    # song was found
    song_uri = result["tracks"]["items"][0]["uri"]
    track_uri.append(song_uri)
    songs_num += 1

# adding the tracks into our playlist
sp.playlist_add_items(playlist_id=playlist_id, items=track_uri, position=None)
print(f"{songs_num} songs added to the playlist")
