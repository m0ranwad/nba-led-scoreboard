import requests
import datetime
import time as t
from utils import convert_time

# Global constant for the NBA scoreboard URL
NBA_SCOREBOARD_URL = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"

def get_moneyline_odds(game_id):
    """
    Fetches the moneyline odds for a given NBA game.

    Args:
        game_id (str): The unique identifier for the game.

    Returns:
        tuple: Moneyline odds for away and home teams, or ("N/A", "N/A") if not found.
    """
    odds_url = f"http://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events/{game_id}/competitions/{game_id}/odds"
    response = requests.get(odds_url)

    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])

        if items:
            first_item = items[0]
            away_team_odds = first_item.get("awayTeamOdds", {})
            home_team_odds = first_item.get("homeTeamOdds", {})

            away_moneyline = away_team_odds.get("moneyLine", "N/A")
            home_moneyline = home_team_odds.get("moneyLine", "N/A")

            away_ml_formatted = f"+{away_moneyline}" if away_moneyline >= 0 else str(away_moneyline)
            home_ml_formatted = f"+{home_moneyline}" if home_moneyline >= 0 else str(home_moneyline)

            return away_ml_formatted, home_ml_formatted

        else:
            print("No items in the response.")
            return "N/A", "N/A"

    else:
        print(f"Request failed with status code: {response.status_code}")
        return "N/A", "N/A"

def get_all_games():
    """
    Fetches all current NBA games with their basic details and moneyline odds.

    Returns:
        list: List of dictionaries, each containing game details and odds.
    """
    try:
        response = requests.get(NBA_SCOREBOARD_URL)
        games_data = response.json().get('events', [])

        games = []
        for game_info in games_data:
            competition_info = game_info['competitions'][0]
            game_id = game_info['id']
            game_state = competition_info['status']['type']['state']

            # Fetch moneyline odds only if the game is in the pre-game state
            if game_state == 'pre':
                away_ml, home_ml = get_moneyline_odds(game_id)
            else:
                away_ml, home_ml = "", ""

            away_ml, home_ml = get_moneyline_odds(game_id)

            game = {
                'name': game_info['shortName'],
                'date': game_info['date'],
                'hometeam': competition_info['competitors'][0]['team']['abbreviation'],
                'homeid': competition_info['competitors'][0]['id'],
                'homescore': int(competition_info['competitors'][0]['score']),
                'awayteam': competition_info['competitors'][1]['team']['abbreviation'],
                'awayid': competition_info['competitors'][1]['id'],
                'awayscore': int(competition_info['competitors'][1]['score']),
                'time': competition_info['status']['displayClock'],
                'quarter': competition_info['status']['period'],
                'over': competition_info['status']['type']['completed'],
                'state': competition_info['status']['type']['state'],
                'away_moneyline': away_ml,
                'home_moneyline': home_ml
            }

            games.append(game)

        return games

    except requests.exceptions.RequestException as e:
        print(f"Error encountered getting game info: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Example usage
if __name__ == "__main__":
    games = get_all_games()
    for game in games:
        print(game)
