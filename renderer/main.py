from PIL import Image, ImageFont, ImageDraw, ImageSequence
from rgbmatrix import graphics
from utils import center_text
from calendar import month_abbr
from renderer.screen_config import screenConfig
from datetime import datetime, timedelta
import time as t
import debug
import re

GAMES_REFRESH_RATE = 900.0

class MainRenderer:
    def __init__(self, matrix, data):
        self.matrix = matrix
        self.data = data
        self.screen_config = screenConfig("64x32_config")
        self.canvas = matrix.CreateFrameCanvas()
        self.width = 64
        self.height = 32
        # Create a new data image.
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        # Load the fonts
        self.font = ImageFont.truetype("fonts/score_large.otf", 16)
        self.font_mini = ImageFont.truetype("fonts/04B_24__.TTF", 8)
        self.font_tiny = ImageFont.truetype("fonts/04B_03__.TTF", 8)

    def refresh_display(self):
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        self.canvas.SetImage(self.image, 0, 0)
        self.canvas = self.matrix.SwapOnVSync(self.canvas)

    def display_nba_logo(self):
        nba_logo = Image.open('/logos/NBA.png').resize((22, 22), Image.ANTIALIAS)
        self.canvas.SetImage(nba_logo.convert("RGB"), 22, 1)

    def display_team_logos(self, game, away_logo_position, home_logo_position):
        """
        Displays team logos on the canvas at specified positions.
        Parameters:
            game: The game data object.
            away_logo_position: A tuple (x, y) for the position of the away team logo.
            home_logo_position: A tuple (x, y) for the position of the home team logo.
        """
        self.canvas.SetImage(self.image, 0, 0)
        if self.data.nba_logos:
            away_team_logo = Image.open('logos/{}H.png'.format(game['awayteam'])).resize((20, 20), Image.ANTIALIAS)
            home_team_logo = Image.open('logos/{}H.png'.format(game['hometeam'])).resize((20, 20), Image.ANTIALIAS)
        else:
            away_team_logo = Image.open('logos/{}.png'.format(game['awayteam'])).resize((20, 20), Image.BOX)
            home_team_logo = Image.open('logos/{}.png'.format(game['hometeam'])).resize((20, 20), Image.BOX)

        self.canvas.SetImage(away_team_logo.convert("RGB"), *away_logo_position)
        self.canvas.SetImage(home_team_logo.convert("RGB"), *home_logo_position)

    def render(self):
        try:
            self.loading()
            self.starttime = t.time()
            self.data.get_current_date()
            self.__render_game()
        except Exception as e:
            print(f"Error: {e}")
            t.sleep(1.2)
            self.error_screen()

    def __render_game(self):
        while True:
            # If we need to refresh the overview data, do that
            if self.data.needs_refresh:
                self.data.refresh_games()

            # Draw the current game
            self.__draw_game(self.data.current_game())

            # Set the refresh rate
            refresh_rate = self.data.config.scrolling_speed
            t.sleep(refresh_rate)
            endtime = t.time()
            time_delta = endtime - self.starttime
            rotate_rate = self.__rotate_rate_for_game(self.data.current_game())

            # If we're ready to rotate, let's do it
            # fix this u idiot
            if time_delta >= rotate_rate:
                self.starttime = t.time()
                self.data.needs_refresh = True

                if self.__should_rotate_to_next_game(self.data.current_game()):
                    game = self.data.advance_to_next_game()

                if endtime - self.data.games_refresh_time >= GAMES_REFRESH_RATE:
                    self.data.refresh_games()

                if self.data.needs_refresh:
                    self.data.refresh_games()

    def __rotate_rate_for_game(self, game):
        rotate_rate = self.data.config.rotation_rates_live
        if game['state'] == 'pre':
            rotate_rate = self.data.config.rotation_rates_pregame
        elif game['state'] == 'post':
            rotate_rate = self.data.config.rotation_rates_final
        return rotate_rate

    def __should_rotate_to_next_game(self, game):
        if self.data.config.rotation_enabled == False:
            return False

        stay_on_preferred_team = self.data.config.preferred_teams and not self.data.config.rotation_preferred_team_live_enabled
        if stay_on_preferred_team == False:
            return True
        else:
            return False

    def __draw_game(self, game):
        """
        Determines the state of the game and calls the appropriate method to draw the game information.
        """
        current_time = self.data.get_current_date()
        gametime = datetime.strptime(game['date'], "%Y-%m-%dT%H:%MZ")

        if game['state'] == 'pre':
            if current_time < gametime - timedelta(hours=1):
                debug.info('Countdown til gametime')
                self._draw_countdown(game)
            else:
                debug.info('Pre-Game State')
                self._draw_pregame(game)
        elif game['state'] == 'post':
            debug.info('Final State')
            self._draw_post_game(game)
        else:
            debug.info('Live State, checking every 5s')
            self._draw_live_game(game)

        debug.info('ping render_game')


    def loading(self):
        loading_pos = center_text(self.font_mini.getsize('Loading')[0], 32)
        self.draw.multiline_text((loading_pos, 24), 'Loading...', font=self.font_mini, align="center")
        self.display_nba_logo()
        self.refresh_display()
        if self.data is not None:
            pass
        elif self.data is None:
            print('NONE')
            pass
        else:
            # Handle the case where data is not passed
            # t.sleep(2)
            print("Error getting Data, ESPN API may be down.")
            t.sleep(30)
            sys.exit(1)


    def error_screen(self):
        self.draw.multiline_text((24, 24), 'Error', fill=(255, 55, 25), font=self.font_mini, align="center")
        self.display_nba_logo()
        self.refresh_display()
        t.sleep(30)
        if self.data is not None:
            pass


    def _draw_pregame(self, game):
        """
        Draws the pre-game state including the date, time, and teams.
        """
        current_time = self.data.get_current_date()
        game_datetime = self.data.get_gametime()

        # Determine the display text based on the game date
        if game_datetime.day == current_time.day:
            date_text = 'TODAY'
        else:
            date_text = game_datetime.strftime('%A %-d %b').upper()
        game_time = game_datetime.strftime("%-I:%M %p")

        # Center the game time on screen
        date_pos = center_text(self.font_mini.getsize(date_text)[0], 32)
        game_time_pos = center_text(self.font_mini.getsize(game_time)[0], 32)

        # Draw the text on the Data image
        self.draw.text((date_pos, 0), date_text, font=self.font_mini)
        self.draw.multiline_text((game_time_pos, 6), game_time, fill=(255, 255, 255), font=self.font_mini, align="center")
        self.draw.text((25, 15), 'VS', font=self.font)

        # Draw the pre-game Moneyline Odds
        self.draw.text((1, 4), game['away_moneyline'], font=self.font_mini, fill=(0, 255, 0))
        self.draw.text((46, 4), game['home_moneyline'], font=self.font_mini, fill=(0, 255, 0))
        # Draw Logos
        self.display_team_logos(game, (1, 12), (43, 12))
        # Load the canvas on screen.
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
        # Refresh the Data image.
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

    def _draw_countdown(self, game):
        """
        Draws the countdown to game start.
        """
        current_time = self.data.get_current_date()
        game_datetime = datetime.strptime(game['date'], "%Y-%m-%dT%H:%MZ")

        # Calculate remaining time until the game
        if current_time < game_datetime:
            remaining_time = game_datetime - current_time
            if remaining_time > timedelta(hours=1):
                countdown = ':'.join(str(remaining_time).split(':')[:2])
            else:
                countdown = ':'.join(str(remaining_time).split(':')[1:]).split('.')[0]

            # Center the countdown on screen
            countdown_pos = center_text(self.font_mini.getsize(countdown)[0], 32)

            # Draw the countdown text
            self.draw.text((29, 0), 'IN', font=self.font_mini)
            self.draw.multiline_text((countdown_pos, 6), countdown, fill=(255, 255, 255), font=self.font_mini, align="center")
            self.draw.text((25, 15), 'VS', font=self.font)

            # Draw the pre-game Moneyline Odds
            self.draw.text((1, 4), game['away_moneyline'], font=self.font_mini, fill=(0, 255, 0))
            self.draw.text((46, 4), game['home_moneyline'], font=self.font_mini, fill=(0, 255, 0))
            # Draw Logos
            self.display_team_logos(game, (1, 12), (43, 12)) 
            # Load the canvas on screen.
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
            # Refresh the Data image.
            self.image = Image.new('RGB', (self.width, self.height))
            self.draw = ImageDraw.Draw(self.image)


    def _draw_live_game(self, game):
        homescore = game['homescore']
        awayscore = game['awayscore']
        print("home: ", homescore, "away: ", awayscore)
        # Refresh the data
        if self.data.needs_refresh:
            debug.info('Refresh game overview')
            self.data.refresh_games()
            self.data.needs_refresh = False
        quarter = str(game['quarter'])
        time_period = game['time']
        
        # Set the position of the information on screen.
        homescore = '{0:02d}'.format(homescore)
        awayscore = '{0:02d}'.format(awayscore)
        home_score_size = self.font.getsize(homescore)[0]
        home_score_pos = center_text(self.font.getsize(homescore)[0], 16)
        away_score_pos = center_text(self.font.getsize(awayscore)[0], 48)
        time_period_pos = center_text(self.font_mini.getsize(time_period)[0], 32)
        # score_position = center_text(self.font.getsize(score)[0], 32)
        quarter_position = center_text(self.font_mini.getsize(quarter)[0], 32)
        # away_odds_position = (2, 26)  # Example position for away team odds
        # home_odds_position = (48, 26)  # Example position for home team odds
        # info_pos = center_text(self.font_mini.getsize(pos)[0], 32)
        # self.draw.multiline_text((info_pos, 13), pos, fill=pos_colour, font=self.font_mini, align="center")

        self.draw.multiline_text((quarter_position, 0), quarter, fill=(255, 255, 255), font=self.font_mini, align="center")
        self.draw.multiline_text((time_period_pos, 6), time_period, fill=(255, 255, 255), font=self.font_mini, align="center")
        self.draw.multiline_text((6, 19), awayscore, fill=(255, 255, 255), font=self.font, align="center")
        self.draw.multiline_text((59 - home_score_size, 19), homescore, fill=(255, 255, 255), font=self.font, align="center")
        # Draw Logos
        self.display_team_logos(game, (1, 0), (43, 0))

        # Load the canvas on screen.
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
        # Refresh the Data image.
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        # Check if the game is over
        if game['state'] == 'post':
            debug.info('GAME OVER')
        # Save the scores.
        # awayscore = game['awayscore']
        # homescore = game['homescore']
        self.data.needs_refresh = True

    def _draw_post_game(self, game):
        # Prepare the data
        score = '{}-{}'.format(game['awayscore'], game['homescore'])
        # Set the position of the information on screen.
        score_position = center_text(self.font.getsize(score)[0], 32)
        # Draw the text on the Data image.
        self.draw.multiline_text((score_position, 19), score, fill=(255, 255, 255), font=self.font, align="center")
        self.draw.multiline_text((26, 0), "END", fill=(255, 255, 255), font=self.font_mini,align="center")
        # Draw Logos
        self.display_team_logos(game, (1, 0), (43, 0))

        # Load the canvas on screen.
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
        # Refresh the Data image.
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
