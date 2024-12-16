# musical-time-machine

Creates a Spotify playlist of the top 100 songs from the specified date in your account.
Obtains the top 100 songs through web-scraping BillBoard 100

/.cache is a file containing the access token in JSON format

Current known issues:
1. Problems with Spotipy API .search() method -- Does not always return desired results -- song is skipped and not added
2. Mismatch in character encoding. Even though the title may look the same, their encodings might mismatch and cause the program to skip the song
3. Different terminology between the program and official Spotify song titles:
4. ..* <song name> by <song artist> could be <song name> by <song artist 1, song artist 2> on Spotify, causing the program to skip
..*<song name> by <song artist> could be <song name> (ft. <song arist>) on Spotify, a mismatch in naming conventions
