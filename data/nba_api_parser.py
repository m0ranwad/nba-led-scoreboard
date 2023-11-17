import requests
import datetime
import time as t
from utils import convert_time

URL = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"

def get_all_games():
    # for i in range(5):
    try:
        res = requests.get(URL)
        res = res.json()
        games = []
        # i = 0
        for g in res['events']:
            info = g['competitions'][0]
            game = {'name': g['shortName'], 'date': g['date'],
                    'hometeam': info['competitors'][0]['team']['abbreviation'], 'homeid': info['competitors'][0]['id'], 'homescore': int(info['competitors'][0]['score']),
                    'awayteam': info['competitors'][1]['team']['abbreviation'], 'awayid': info['competitors'][1]['id'], 'awayscore': int(info['competitors'][1]['score']),
                    'time': info['status']['displayClock'], 'quarter': info['status']['period'], 'over': info['status']['type']['completed'], 'state': info['status']['type']['state']}
            games.append(game)
            # i += 1
        return games
    except requests.exceptions.RequestException as e:
        print("Error encountered getting game info, can't hit ESPN api, retrying")
        # if i < 4:
        #     t.sleep(1)
        #     continue
        # else:
        #     print("Can't hit ESPN api after multiple retries, dying ", e)
    except Exception as e:
        print("something bad?", e)