from odds_api import odds_api

def test_api():
    print("Testing Odds API connection...")
    
    # Test live games
    print("\nFetching live games...")
    live_games = odds_api.get_live_games()
    print(f"Number of live games: {len(live_games)}")
    for game in live_games:
        print(f"Live game: {game['team1']} vs {game['team2']}")
        if 'score' in game:
            print(f"Score: {game['score']['team1']} - {game['score']['team2']}")
        print(f"Odds: {game['odds']['team1']} - {game['odds']['team2']}")
        print("---")
    
    # Test upcoming games
    print("\nFetching upcoming games...")
    upcoming_games = odds_api.get_upcoming_games()
    print(f"Number of upcoming games: {len(upcoming_games)}")
    for game in upcoming_games:
        print(f"Upcoming game: {game['team1']} vs {game['team2']}")
        print(f"Date: {game['date']}")
        print(f"Odds: {game['odds']['team1']} - {game['odds']['team2']}")
        print("---")

if __name__ == "__main__":
    test_api() 