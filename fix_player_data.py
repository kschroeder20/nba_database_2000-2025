"""
Fix data quality issues in the players table:
1. Draft rounds > 2 should be capped at 2 (NBA has only 2 rounds since 1989)
2. Shoots should be only 'Left' or 'Right' (normalize 'LeftRight' to 'Left', 'RightRight' to 'Right')
3. Verify undrafted players are properly recorded
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import time
import re

DB_PATH = "nba.db"
BASE_URL = "https://www.basketball-reference.com"
DELAY = 3

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fix_existing_data():
    """Fix the data quality issues in the existing database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=== Fixing Existing Data ===\n")

    # 1. Fix draft rounds > 2
    print("1. Fixing draft rounds > 2...")
    cursor.execute("SELECT player_id, full_name, draft_round FROM players WHERE draft_round > 2")
    invalid_rounds = cursor.fetchall()

    if invalid_rounds:
        print(f"   Found {len(invalid_rounds)} players with draft_round > 2:")
        for player_id, name, round_num in invalid_rounds:
            print(f"   - {name}: round {round_num} -> 2")

        cursor.execute("UPDATE players SET draft_round = 2 WHERE draft_round > 2")
        print(f"   ✅ Updated {cursor.rowcount} players to round 2\n")
    else:
        print("   ✅ No invalid draft rounds found\n")

    # 2. Fix shoots column
    print("2. Fixing shoots column...")
    cursor.execute("SELECT player_id, full_name, shoots FROM players WHERE shoots LIKE '%Left%' AND shoots != 'Left'")
    left_issues = cursor.fetchall()

    cursor.execute("SELECT player_id, full_name, shoots FROM players WHERE shoots LIKE '%Right%' AND shoots != 'Right'")
    right_issues = cursor.fetchall()

    if left_issues:
        print(f"   Found {len(left_issues)} players with 'LeftRight' or similar:")
        for player_id, name, shoots in left_issues:
            print(f"   - {name}: '{shoots}' -> 'Left'")
        cursor.execute("UPDATE players SET shoots = 'Left' WHERE shoots LIKE '%Left%' AND shoots != 'Left'")
        print(f"   ✅ Updated {cursor.rowcount} players\n")

    if right_issues:
        print(f"   Found {len(right_issues)} players with 'RightLeft' or similar:")
        for player_id, name, shoots in right_issues:
            print(f"   - {name}: '{shoots}' -> 'Right'")
        cursor.execute("UPDATE players SET shoots = 'Right' WHERE shoots LIKE '%Right%' AND shoots != 'Right'")
        print(f"   ✅ Updated {cursor.rowcount} players\n")

    if not left_issues and not right_issues:
        print("   ✅ No invalid shoots values found\n")

    # 3. Check undrafted players
    print("3. Checking undrafted players...")
    cursor.execute("SELECT COUNT(*) FROM players WHERE draft_round IS NULL")
    undrafted_count = cursor.fetchone()[0]
    print(f"   ℹ️  {undrafted_count} undrafted players (NULL draft_round is correct)\n")

    conn.commit()
    conn.close()

    print("=== Data Fix Complete ===\n")


def normalize_shoots(shoots_text):
    """Normalize shooting hand to just 'Left' or 'Right'."""
    if not shoots_text:
        return None

    shoots_text = shoots_text.strip()

    # Check for left-handed (prioritize left in ambiguous cases)
    if 'Left' in shoots_text or 'left' in shoots_text.lower():
        return 'Left'
    elif 'Right' in shoots_text or 'right' in shoots_text.lower():
        return 'Right'

    return shoots_text


def normalize_draft_round(round_num):
    """Normalize draft round to max of 2 (NBA has 2 rounds since 1989)."""
    if round_num is None:
        return None

    try:
        round_int = int(round_num)
        # Cap at 2 since NBA draft has been 2 rounds since 1989
        return min(round_int, 2)
    except (ValueError, TypeError):
        return None


def test_scrape_player(player_id):
    """Test the updated scraping logic on a specific player."""
    first_letter = player_id[0]
    url = f"{BASE_URL}/players/{first_letter}/{player_id}.html"

    print(f"Testing scrape for player: {player_id}")
    print(f"URL: {url}")

    time.sleep(DELAY)
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Name
    full_name = ""
    heading = soup.find("h1")
    if heading:
        name_span = heading.find("span")
        if name_span:
            full_name = name_span.get_text(strip=True)
        else:
            full_name = heading.get_text(strip=True)

    # Initialize
    shoots = None
    draft_year = None
    draft_round = None
    draft_pick = None
    draft_team = None

    # Meta section
    meta_div = soup.find("div", {"id": "meta"})
    if meta_div:
        paragraphs = meta_div.find_all("p")

        for paragraph in paragraphs:
            text = paragraph.get_text(strip=True)

            # Shooting hand
            if "Shoots:" in text:
                shoots_match = re.search(r'Shoots:\s*(\S+)', text)
                if shoots_match:
                    raw_shoots = shoots_match.group(1).strip()
                    shoots = normalize_shoots(raw_shoots)
                    print(f"  Shoots: '{raw_shoots}' -> '{shoots}'")

            # Draft info
            if "Draft:" in text:
                # Check for "Undrafted"
                if "Undrafted" in text or "undrafted" in text:
                    print(f"  Draft: Undrafted (will store as NULL)")
                    draft_round = None
                    draft_pick = None
                    draft_team = None
                    draft_year = None
                else:
                    draft_team_match = re.search(r'Draft:\s*(.+?),', text)
                    if draft_team_match:
                        draft_team = draft_team_match.group(1).strip()

                    round_match = re.search(r'(\d+)\w*\s*round', text)
                    if round_match:
                        raw_round = int(round_match.group(1))
                        draft_round = normalize_draft_round(raw_round)
                        if raw_round != draft_round:
                            print(f"  Draft Round: {raw_round} -> {draft_round} (capped)")
                        else:
                            print(f"  Draft Round: {draft_round}")

                    pick_match = re.search(r'(\d+)\w*\s*pick', text)
                    if pick_match:
                        draft_pick = int(pick_match.group(1))
                        print(f"  Draft Pick: {draft_pick}")

                    year_match = re.search(r'(\d{4})\s*NBA\s*Draft', text)
                    if year_match:
                        draft_year = int(year_match.group(1))
                        print(f"  Draft Year: {draft_year}")

                    if draft_team:
                        print(f"  Draft Team: {draft_team}")

    return {
        "name": full_name,
        "shoots": shoots,
        "draft_year": draft_year,
        "draft_round": draft_round,
        "draft_pick": draft_pick,
        "draft_team": draft_team
    }


def main():
    print("NBA Player Data Fix Script")
    print("=" * 50)
    print()

    # Fix existing data
    fix_existing_data()

    # Test scraping logic on a few players
    print("=== Testing Updated Scraping Logic ===\n")

    # Get some test cases from the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Test case 1: Player with shoots issue
    print("Test 1: Player with potential shoots issue")
    test_scrape_player("bryanko01")  # Kobe Bryant
    print()

    # Test case 2: Undrafted player
    print("Test 2: Undrafted player")
    cursor.execute("SELECT player_id FROM players WHERE draft_round IS NULL LIMIT 1")
    result = cursor.fetchone()
    if result:
        test_scrape_player(result[0])
    print()

    # Test case 3: First round pick
    print("Test 3: First round pick")
    test_scrape_player("jamesle01")  # LeBron James
    print()

    conn.close()

    print("=== All Tests Complete ===")

    # Final validation
    print("\n=== Final Validation ===\n")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT shoots, COUNT(*) FROM players GROUP BY shoots ORDER BY shoots")
    print("Shoots distribution:")
    for row in cursor.fetchall():
        print(f"  {row[0] if row[0] else 'NULL'}: {row[1]}")

    print()
    cursor.execute("SELECT draft_round, COUNT(*) FROM players GROUP BY draft_round ORDER BY draft_round")
    print("Draft round distribution:")
    for row in cursor.fetchall():
        print(f"  Round {row[0] if row[0] else 'NULL (undrafted)'}: {row[1]}")

    conn.close()

    print("\n✅ Script complete!")


if __name__ == "__main__":
    main()
