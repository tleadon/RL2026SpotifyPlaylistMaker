import requests
import time
import json

SONGS_PER_TIER = {
    1: 7,
    2: 5,
    3: 3,
    4: 2,
    5: 1,
}

TEST_LINEUP = {
    1: ["Don Toliver", "Playboi Carti", "NBA YoungBoy"],
    2: ["EsdeeKid", "Chief Keef", "Sahbabii", "Nettspend", "Xaviersobased", "SoFayGo", "Destroy Lonely", "Fakemink", "Pooh Shiesty", "Homixide Gang", "Nine Vicious", "Sexyy Red", "Bossman Dlow", "NoCap", "Osamason", "Che", "Plaqueboymax"],
    3: ["Luh Tyler", "1900Rugrat", "Nino Paid", "Lazer Dim 700", "Hotboii", "Fimiguerro", "yt", "babychiefdoit", "skai isyourgod", "tiacorine", "feng", "molly santana", "f1lthy", "Loeshimmy", "skrilla", "hurricane wisdom", "hemzzz", "skaiwater", "lucy bedroque"],
    4: ["Sosocamo", "Lelo", "Chow Lee", "Belly Gang Kushington", "Yung Fazo", "Jorjiana", "Lil Wet", "Savv4x", "Big3D", "Chuckyy", "Raq Baby", "Bloodhound Q50", "UntilJapan", "Karrahbooo", "Nino Breeze", "Protect", "Danny Towers", "Ykniece", "10neam", "ffawty", "adamn killa", "dogiemane", "b2b", "ilykimchi"],
    5: ["El Snappo", "Tezzus", "SixBill", "K3", "Percaso", "Floor 13", "B Jacks", "Apollored1", "Rosama", "Baby Mel", "Hooligan Hefs", "Clip", "Yume", "Kelsi", "Sorisa", "Sowayv", "Champgne937", "Pradabagshawty", "1300Saint", "Diorvsyou", "ohsxnta", "slayr", "jayy wick", "goldenboy countup", "trim", "flogo", "OC Chris", "Thirteendegrees", "bigwestt"]
}

# =============================================================================
# DEEZER API
# =============================================================================

DEEZER_BASE_URL = "https://api.deezer.com"


def search_artist(artist_name: str) -> dict | None:
    """Search for an artist on Deezer and return the best match."""
    url = f"{DEEZER_BASE_URL}/search/artist"
    params = {"q": artist_name}

    response = requests.get(url, params=params)
    data = response.json()

    if data.get("data") and len(data["data"]) > 0:
        return data["data"][0]  # Return best match
    return None


def get_top_tracks(artist_id: int, limit: int = 5) -> list[dict]:
    """Get top tracks for an artist by their Deezer ID."""
    url = f"{DEEZER_BASE_URL}/artist/{artist_id}/top"
    params = {"limit": limit}

    response = requests.get(url, params=params)
    data = response.json()

    return data.get("data", [])

def build_playlist(lineup: dict[int, list[str]]) -> list[dict]:
    """
    Build a playlist from the lineup.
    Returns a list of track info dicts with artist, track name, etc.
    """
    playlist = []

    for tier, artists in lineup.items():
        songs_to_fetch = SONGS_PER_TIER.get(tier, 1)
        print(f"\n{'='*50}")
        print(f"TIER {tier} - Fetching {songs_to_fetch} songs per artist")
        print(f"{'='*50}")

        for artist_name in artists:
            print(f"\nSearching for: {artist_name}")

            artist = search_artist(artist_name)
            if not artist:
                print(f"  [!] Could not find artist: {artist_name}")
                continue

            print(f"  [OK] Found: {artist['name']} (ID: {artist['id']}, Fans: {artist.get('nb_fan', 'N/A'):,})")

            tracks = get_top_tracks(artist["id"], limit=songs_to_fetch)

            for track in tracks:
                track_info = {
                    "artist_name": artist["name"],
                    "artist_id": artist["id"],
                    "track_name": track["title"],
                    "track_id": track["id"],
                    "album": track.get("album", {}).get("title", "Unknown"),
                    "duration": track.get("duration", 0),
                    "tier": tier,
                }
                playlist.append(track_info)
                # Encode safely for Windows console
                safe_title = track['title'].encode('ascii', 'replace').decode('ascii')
                print(f"    - {safe_title}")

            # Be nice to the API
            time.sleep(0.25)

    return playlist


def print_playlist_summary(playlist: list[dict]) -> None:
    """Print a summary of the generated playlist."""
    print(f"\n{'='*50}")
    print("PLAYLIST SUMMARY")
    print(f"{'='*50}")
    print(f"Total tracks: {len(playlist)}")

    # Group by tier
    tier_counts = {}
    for track in playlist:
        tier = track["tier"]
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    print("\nTracks by tier:")
    for tier in sorted(tier_counts.keys()):
        print(f"  Tier {tier}: {tier_counts[tier]} tracks")

    # Calculate total duration
    total_seconds = sum(track["duration"] for track in playlist)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    print(f"\nTotal duration: {hours}h {minutes}m")

def save_playlist(playlist: list[dict], filepath: str = "playlist.json") -> None:
    """Save playlist to JSON file for Spotify automation."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(playlist, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Playlist saved to {filepath}")

def main():
    print("Rolling Loud 2026 Playlist Builder")
    print("===================================\n")

    # Build the playlist from the lineup
    playlist = build_playlist(TEST_LINEUP)

    # Print summary
    print_playlist_summary(playlist)

    # Save playlist to JSON
    save_playlist(playlist)

    print("\n" + "=" * 50)
    print("Next step: Run spotify_automation.py to add songs to Spotify")
    print("  venv/Scripts/python spotify_automation.py")
    print("=" * 50)


if __name__ == "__main__":
    main()
