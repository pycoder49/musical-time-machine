from collections import namedtuple
from datetime import datetime
from bs4 import BeautifulSoup
import pprint as pp
import requests
import spotipy
import os

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
HEADER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0"}
CACHE_PATH = ".cache"


def get_user_input() -> tuple[str, str] | None:
    # getting user input
    user_date = input("What year do you want your playlist to be based on? (YYYY-MM-DD): ")

    # validating user input
    try:
        valid_date = datetime.strptime(user_date, "%Y-%m-%d")
    except ValueError:
        return None

    song_year = user_date.split("-")[0]

    return user_date, song_year


# scraping the BillBoard and getting the top 100 songs and artists
def get_top100(browser_header: dict[str, str], user_date: str) -> tuple[list, list] | None:
    url = "https://www.billboard.com/charts/hot-100/" + user_date

    try:
        response = requests.get(url=url, headers=browser_header)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

    top_100 = response.text

    soup = BeautifulSoup(top_100, "html.parser")

    song_tags = soup.select("li ul li h3")
    song_artist_tags = soup.select("li ul li .c-label.a-no-trucate")

    song_titles = [tag.getText().strip() for tag in song_tags]
    song_artists = [artist.getText().strip() for artist in song_artist_tags]

    return song_titles, song_artists


def create_user_playlist(sp: spotipy.Spotify, date: str, year: str) -> str:
    # obtain user info
    current_user = sp.current_user()
    current_user_id = current_user["id"]

    # creating a playlist
    playlist = sp.user_playlist_create(
        user=current_user_id,
        name=f"{date} Top 100 Songs",
        public=False,
        description=f"Top hundred songs from the year {year}"
    )
    playlist_id = playlist["id"]
    return playlist_id


def add_songs(
    sp: spotipy.Spotify,
    song_titles: list,
    song_artists: list,
    playlist_id: str,
    year: str
) -> tuple[int, list]:
    # searching for each song, and then getting its track
    # if song not on Spotify, print skipped
    BadSong = namedtuple("BadSong", ["expected_title", "expected_artist", "found_title", "found_arist"])
    bad_songs = []
    track_uri = []
    songs_num = 0
    for song_name, song_artist in zip(song_titles, song_artists):
        try:
            query = f"artist: {song_artist} track: {song_name} year: {year}"
            result = sp.search(q=query, type="track", limit=1)
        except IndexError:
            print(f"{song_name} by {song_artist} not found on Spotify --> skipped.")
            continue

        # extra check in case wrong song was found
        current_track = result["tracks"]["items"][0]
        current_song_name = current_track["name"]
        current_song_artist = current_track["artists"][0]["name"]

        if (current_song_name.strip().lower() != song_name.strip().lower()
                or current_song_artist.strip().lower() != song_artist.strip().lower()):
            bad_songs.append(BadSong(song_name, song_artist, current_song_name, current_song_artist))
            continue

        # song was found
        song_uri = current_track["uri"]
        track_uri.append(song_uri)
        songs_num += 1

    # adding the tracks into our playlist
    sp.playlist_add_items(playlist_id=playlist_id, items=track_uri, position=None)
    return songs_num, bad_songs


def main():
    user_date = get_user_input()
    if not user_date:
        print("Invalid date/invalid format")
        quit()

    song_titles, song_artists = get_top100(HEADER, user_date[0])
    if not song_titles or not song_artists:
        print("Something didn't work out, try again")
        quit()

    sp = spotipy.Spotify(
        auth_manager=spotipy.SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri="http://example.com",
            scope="playlist-modify-private",
            cache_path=CACHE_PATH,
            show_dialog=True
        ))

    playlist_id = create_user_playlist(sp, user_date[0], user_date[1])
    songs_added, bad_songs = add_songs(sp, song_titles, song_artists, playlist_id, user_date[1])

    print(f"Total number of songs added: {songs_added}")
    pp.pprint(bad_songs)


if __name__ == "__main__":
    main()
