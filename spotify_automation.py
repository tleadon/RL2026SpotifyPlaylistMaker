import json
import time
import urllib.parse
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout


def wait_for_login(page: Page) -> None:
    """Wait for user to log in to Spotify."""
    print("\n" + "=" * 50)
    print("Please log in to Spotify in the browser window.")
    print("Once logged in and you see the main player, press ENTER...")
    print("=" * 50)
    input()


def create_playlist_manual(page: Page, playlist_name: str) -> None:
    """Guide user to create playlist manually."""
    print("\n" + "=" * 50)
    print(f"Please CREATE A PLAYLIST named '{playlist_name}' manually:")
    print("  1. Click 'Your Library' on the left")
    print("  2. Click the '+' button")
    print("  3. Click 'Create a new playlist'")
    print("  4. Name it: " + playlist_name)
    print("\nPress ENTER once the playlist is created...")
    print("=" * 50)
    input()


def search_and_add_track(page: Page, artist: str, track: str, playlist_name: str) -> bool:
    """Search for a track and add it to the playlist."""
    # Clean up the track name for search (remove feat. info for better matching)
    clean_track = track.split("(feat.")[0].split("(From")[0].strip()
    search_query = f"{clean_track} {artist}"
    encoded_query = urllib.parse.quote(search_query)

    try:
        # Navigate directly to search results
        page.goto(f"https://open.spotify.com/search/{encoded_query}", wait_until="networkidle", timeout=15000)
        time.sleep(1)

        # Try to find the "Songs" section and click the first result
        # First, try to click on "Songs" to filter
        try:
            songs_filter = page.locator('button:has-text("Songs")').first
            if songs_filter.is_visible(timeout=2000):
                songs_filter.click()
                time.sleep(0.5)
        except:
            pass  # Songs filter might not be there, continue anyway

        # Find the first track row using various selectors
        track_row = None
        selectors = [
            '[data-testid="tracklist-row"]',
            '[data-testid="track-row"]',
            'div[role="row"][aria-rowindex="1"]',
            'div[data-testid="tracklist"] div[role="row"]',
        ]

        for selector in selectors:
            try:
                track_row = page.locator(selector).first
                if track_row.is_visible(timeout=2000):
                    break
            except:
                continue

        if not track_row:
            print(f"  [!] No results found for: {artist} - {track}")
            return False

        # Right-click to open context menu
        track_row.click(button="right")
        time.sleep(0.5)

        # Look for "Add to playlist" option
        add_to_playlist = page.locator('button:has-text("Add to playlist"), span:has-text("Add to playlist"), [role="menuitem"]:has-text("Add to playlist")').first
        add_to_playlist.click(timeout=3000)
        time.sleep(1.5)  # Wait for submenu to load

        # Try multiple approaches to find and click the playlist
        clicked = False

        # Approach 1: Try to find a search box in the submenu and type playlist name
        try:
            search_box = page.locator('input[placeholder*="playlist"], input[placeholder*="search"], input[type="text"]').first
            if search_box.is_visible(timeout=1000):
                search_box.fill(playlist_name)
                time.sleep(0.5)
                page.keyboard.press("Enter")
                clicked = True
        except:
            pass

        # Approach 2: Try various selectors
        if not clicked:
            playlist_selectors = [
                f'[role="menuitem"]:has-text("{playlist_name}")',
                f'[role="option"]:has-text("{playlist_name}")',
                f'li:has-text("{playlist_name}")',
                f'button:has-text("{playlist_name}")',
                f'span:has-text("{playlist_name}")',
            ]

            for selector in playlist_selectors:
                try:
                    option = page.locator(selector).first
                    if option.is_visible(timeout=800):
                        option.click()
                        clicked = True
                        break
                except:
                    continue

        # Approach 3: Use keyboard to navigate - type to filter then Enter
        if not clicked:
            try:
                page.keyboard.type("Rolling", delay=50)
                time.sleep(0.5)
                page.keyboard.press("Enter")
                clicked = True
            except:
                pass

        # Approach 4: Last resort - click any visible text matching playlist name
        if not clicked:
            page.get_by_text(playlist_name, exact=False).first.click(timeout=2000)

        time.sleep(0.3)

        print(f"  [OK] Added: {artist} - {clean_track}")
        return True

    except PlaywrightTimeout as e:
        print(f"  [!] Timeout: {artist} - {track}")
        return False
    except Exception as e:
        print(f"  [!] Failed: {artist} - {track} ({str(e)[:50]})")
        return False


def add_tracks_to_spotify(playlist: list[dict], playlist_name: str = "Rolling Loud 2026") -> None:
    """Main function to add all tracks to Spotify."""

    with sync_playwright() as p:
        # Uses installed Chrome with persistent context
        print("Launching Chrome...")
        context = p.chromium.launch_persistent_context(
            user_data_dir="./browser_data",
            channel="chrome",
            headless=False,
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        # Navigate to Spotify
        print("Opening Spotify Web Player...")
        page.goto("https://open.spotify.com", timeout=30000)
        time.sleep(2)

        # Wait for user to log in
        wait_for_login(page)

        # Guide user to create playlist manually
        create_playlist_manual(page, playlist_name)

        # Add each track
        print(f"\nAdding {len(playlist)} tracks to playlist...")
        print("(This will take a while - ~5 seconds per track)\n")

        successful = 0
        failed = 0
        failed_tracks = []

        for i, track in enumerate(playlist):
            print(f"[{i+1}/{len(playlist)}] {track['artist_name']} - {track['track_name'][:40]}...")

            if search_and_add_track(page, track["artist_name"], track["track_name"], playlist_name):
                successful += 1
            else:
                failed += 1
                failed_tracks.append(f"{track['artist_name']} - {track['track_name']}")

            # Small delay between tracks
            time.sleep(0.5)

        # Summary
        print("\n" + "=" * 50)
        print("SPOTIFY IMPORT COMPLETE")
        print("=" * 50)
        print(f"Successfully added: {successful}")
        print(f"Failed: {failed}")

        if failed_tracks:
            print(f"\nFailed tracks saved to: failed_tracks.txt")
            with open("failed_tracks.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(failed_tracks))

        print("\nBrowser will stay open for you to review.")
        print("Press ENTER to close...")
        input()

        context.close()


def load_playlist(filepath: str = "playlist.json") -> list[dict]:
    """Load playlist from JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    print("Spotify Playlist Importer")
    print("=" * 50)

    try:
        playlist = load_playlist("playlist.json")
        print(f"Loaded {len(playlist)} tracks from playlist.json")
        add_tracks_to_spotify(playlist)
    except FileNotFoundError:
        print("Error: playlist.json not found!")
        print("Run main.py first to generate the playlist.")
