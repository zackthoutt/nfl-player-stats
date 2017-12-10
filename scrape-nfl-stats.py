import requests
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool
import time
import shutil
import re
import os
import json
import string
import glob

BASE_URL = 'https://www.pro-football-reference.com{0}'
PLAYER_LIST_URL = 'https://www.pro-football-reference.com/players/{0}'
PLAYER_PROFILE_URL = 'https://www.pro-football-reference.com/players/{0}/{1}'
PLAYER_GAMELOG_URL = 'https://www.pro-football-reference.com/players/{0}/{1}/gamelog/{2}'

HEADERS = {
    'user-agent': ('Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36')
}

PROFILE_DIR = 'profile_data'
STATS_DIR = 'stats_data'

class Scraper():
    """Scraper for pro-football-reference.com to collect NFL player stats"""

    def __init__(self, letters_to_scrape=['A'], num_jobs=1, clear_old_data=True, first_player_id=1):
        """Initialize the scraper to get player stats

                Args:
                    - letters_to_scrape (str[]): The site sorts players by the first letter of their
                      last name. This array tells the scraper which letters to scrape data for.
                    - num_jobs (int): Number of concurrent jobs the scraper should run. While Python
                      can't multi-thread, it can manage multiple processes at once, which allows it to
                      utilize time spent waiting for the server to respond.
                    - clear_old_data (boolean): Whether or not the data file should be wiped before
                      starting the scrape.
                    - first_player_id (int): The first ID for a player (set if you are rerunning to avoid duplicates)

                Returns:
                    None
        """
        self.letters_to_scrape = [letter.upper() for letter in letters_to_scrape]
        self.num_jobs = num_jobs
        self.clear_old_data = clear_old_data
        self.session = requests.Session()
        self.start_time = time.time()
        self.cross_process_player_count = 0
        self.first_player_id = first_player_id

        if num_jobs > 1:
            self.multiprocessing = True
            self.worker_pool = Pool(num_jobs)
        else:
            self.multiprocessing = False

    def scrape_site(self):
        """Pool workers to scrape players by first letter of last name"""
        if self.clear_old_data:
            self.clear_data()
        player_id = self.first_player_id
        for letter in self.letters_to_scrape:
            player_profile_urls = self.get_players_for_letter(letter)
            for player_profile_url in player_profile_urls:
                player = Player(player_id, player_profile_url, self)
                try:
                    player.scrape_profile()
                    player.scrape_player_stats()
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    print('There was a problem parsing stats for {}'.format(player_profile_url))
                    continue
                self.save_player_profile(player.profile)
                self.save_player_game_stats(player.game_stats, player.player_id, player.profile['name'])
                player_id += 1
        self.condense_data()

    def condense_data(self):
        """Condense data into two files, a profile file and a stats file"""
        print('Condensing Data...')
        condensed_profile_data = []
        all_profile_files = glob.glob('{}/*.json'.format(PROFILE_DIR))
        for file in all_profile_files:
            with open(file, 'rb') as fin:
                condensed_profile_data.append(json.load(fin))
        print('{} player profiles condensed'.format(len(condensed_profile_data)))
        filename = 'profiles_{}.json'.format(time.time())
        with open(filename, 'w') as fout:
            json.dump(condensed_profile_data, fout)

        condensed_game_data = []
        all_game_files = glob.glob('{}/*.json'.format(STATS_DIR))
        for file in all_game_files:
            with open(file, 'rb') as fin:
                condensed_game_data += json.load(fin)
        print('{} player seasons condensed'.format(len(condensed_game_data)))
        filename = 'games_{}.json'.format(time.time())
        with open(filename, 'w') as fout:
            json.dump(condensed_game_data, fout)

    def save_player_profile(self, profile):
        """Save a player's profile as JSON

            Args:
                - profile (dict): Player profile data

            Return:
                None
        """
        filename = '{}/{}_{}.json'.format(PROFILE_DIR, profile['player_id'], profile['name'].replace(' ', '-'))
        try:
            os.makedirs(PROFILE_DIR)
        except OSError:
            pass
        with open(filename, 'w') as fout:
            json.dump(profile, fout)

    def save_player_game_stats(self, games, player_id, player_name):
        """Save a list of player games with stats info

            Args:
                - games (dict[]): List of game stats
                - player_id (int): ID of the player the games belong to
                - player_name (str): Name of the player the game stats belong to

            Return:
                None
        """
        filename = '{}/{}_{}.json'.format(STATS_DIR, player_id, player_name.replace(' ', '-'))
        try:
            os.makedirs(STATS_DIR)
        except OSError:
            pass
        with open(filename, 'w') as fout:
            json.dump(games, fout)

    def get_players_for_letter(self, letter):
        """Get a list of player links for a letter of the alphabet.
            Site organizes players by first letter of last name.

            Args:
                - letter (str): letter of the alphabet uppercased

            Returns:
                - player_links (str[]): the URLs to get player profiles
        """
        response = self.get_page(PLAYER_LIST_URL.format(letter))
        soup = BeautifulSoup(response.content, 'html.parser')

        players = soup.find('div', {'id': 'div_players'}).find_all('a')
        return [BASE_URL.format(player['href']) for player in players]

    def get_page(self, url, retry_count=0):
        """Use requests to get a page; retry when failures occur

            Args:
                - url (str): The URL of the page to make a GET request to
                - retry_count (int): Number of times the URL has already been requests

            Returns:
                - response (obj): The Requests response object
        """
        try:
            return self.session.get(url, headers=HEADERS)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            retry_count += 1
            if retry_count <= 3:
                self.session = requests.Session()
                return self.get_page(url, retry_count)
            else:
                raise

    def clear_data(self):
        """Clear the data directories"""
        try:
            shutil.rmtree(PROFILE_DIR)
        except FileNotFoundError:
            pass
        try:
            shutil.rmtree(STATS_DIR)
        except FileNotFoundError:
            pass


class Player():
    """An NFL player"""

    def __init__(self, player_id, profile_url, scraper):
        """
            Args:
                - player_id (int): Unique ID for player
                - profile_url (str): URL to the player's profile
                - scraper (obj): instance of Scraper class

            Returns:
                None
        """
        self.player_id = player_id
        self.profile_url = profile_url
        self.scraper = scraper
        self.profile = {
            'player_id': player_id,
            'name': None,
            'position': None,
            'height': None,
            'weight': None,
            'current_team': None,
            'birth_date': None,
            'birth_place': None,
            'death_date': None,
            'college': None,
            'high_school': None,
            'draft_team': None,
            'draft_round': None,
            'draft_position': None,
            'draft_year': None,
            'current_salary': None,
            'hof_induction_year': None
        }
        self.seasons_with_stats = []
        self.game_stats = []

    def scrape_profile(self):
        """Scrape profile info for player"""
        response = self.scraper.get_page(self.profile_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        profile_section = soup.find('div', {'id': 'meta'})
        self.profile['name'] = profile_section.find('h1', {'itemprop': 'name'}).contents[0]
        print('scaping {}'.format(self.profile['name']))

        profile_attributes = profile_section.find_all('p')
        current_attribute = 1
        num_attributes = len(profile_attributes)

        self.profile['position'] = profile_attributes[current_attribute].contents[2].split('\n')[0].split(' ')[1]
        current_attribute += 1

        height = profile_attributes[current_attribute].find('span', {'itemprop': 'height'})
        if height is not None:
            self.profile['height'] = height.contents[0]
        weight = profile_attributes[current_attribute].find('span', {'itemprop': 'weight'})
        if weight is not None:
            self.profile['weight'] = weight.contents[0].split('lb')[0]
        if height is not None or weight is not None:
            current_attribute += 1

        affiliation_section = profile_section.find('span', {'itemprop': 'affiliation'})
        if affiliation_section is not None:
            self.profile['current_team'] = affiliation_section.contents[0].contents[0]
            current_attribute += 1

        birth_date = profile_attributes[current_attribute].find('span', {'itemprop': 'birthDate'})
        if birth_date is not None:
            self.profile['birth_date'] = birth_date['data-birth']
        birth_place_section = profile_attributes[current_attribute].find('span', {'itemprop': 'birthPlace'}).contents
        try:
            self.profile['birth_place'] = re.split('\xa0', birth_place_section[0])[1] + ' ' + birth_place_section[1].contents[0]
        except IndexError:
            pass
        if birth_date is not None or len(birth_place_section) > 0:
            current_attribute += 1

        death_section = profile_section.find('span', {'itemprop': 'deathDate'})
        if death_section is not None:
            self.profile['death_date'] = death_section['data-death']
            current_attribute += 1

        if profile_attributes[current_attribute].contents[0].contents[0] == 'College':
            self.profile['college'] = profile_attributes[current_attribute].contents[2].contents[0]
            current_attribute += 1

        # Skip weighted career AV
        current_attribute += 1

        if ((current_attribute + 1) <= num_attributes) and profile_attributes[current_attribute].contents[0].contents[0] == 'High School':
            self.profile['high_school'] = profile_attributes[current_attribute].contents[2].contents[0] + ', ' + profile_attributes[current_attribute].contents[4].contents[0]
            current_attribute += 1

        if ((current_attribute + 1) <= num_attributes) and profile_attributes[current_attribute].contents[0].contents[0] == 'Draft':
            self.profile['draft_team'] = profile_attributes[current_attribute].contents[2].contents[0]
            draft_info = profile_attributes[current_attribute].contents[3].split(' ')
            self.profile['draft_round'] = re.findall(r'\d+', draft_info[3])[0]
            self.profile['draft_position'] = re.findall(r'\d+', draft_info[5])[0]
            self.profile['draft_year'] = re.findall(r'\d+', profile_attributes[current_attribute].contents[4].contents[0])[0]
            current_attribute += 1

        if ((current_attribute + 1) <= num_attributes) and profile_attributes[current_attribute].contents[0].contents[0] == 'Current cap hit':
            profile_attributes[current_attribute].contents
            self.profile['current_salary'] = profile_attributes[current_attribute].contents[2].contents[0]
            current_attribute += 1

        if ((current_attribute + 1) <= num_attributes) and profile_attributes[current_attribute].contents[0].contents[0] == 'Hall of fame':
            self.profile['hof_induction_year'] = profile_attributes[current_attribute].contents[2].contents[0]
            current_attribute += 1

        self.seasons_with_stats = self.get_seasons_with_stats(soup)

    def scrape_player_stats(self):
        """Scrape the stats for all available games for a player"""
        for season in self.seasons_with_stats:
            if season['year'] == 'Career' or season['year'] == 'Postseason':
                continue
            self.scrape_season_gamelog(season['gamelog_url'], season['year'])

    def scrape_season_gamelog(self, gamelog_url, year):
        """Scrape player stats for a given year

            Args:
                - gamelog_url (str): URL to the stats for a given year
                - year (int): The year the stats are for

            Returns:
                - stats (dict): All of the player's stats for that year
        """
        response = self.scraper.get_page(gamelog_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        regular_season_table = soup.find('table', {'id': 'stats'})
        if regular_season_table is None:
            return False
        games = regular_season_table.find('tbody').find_all('tr')

        playoff_table = soup.find('table', {'id': 'stats_playoffs'})
        if playoff_table is not None:
            games += playoff_table.find('tbody').find_all('tr')

        for game in games:
            stats = self.make_player_game_stats(self.player_id, year)
            stats['game_id'] = game.find('td', {'data-stat': 'game_date'}).find('a', href=True)['href'].replace('/boxscores/', '').replace('.htm', '')
            stats['date'] = game.find('td', {'data-stat': 'game_date'}).contents[0].contents[0]
            stats['game_number'] = game.find('td', {'data-stat': 'game_num'}).contents[0]
            stats['age'] = game.find('td', {'data-stat': 'age'}).contents[0]
            stats['team'] = game.find('td', {'data-stat': 'team'}).contents[0].contents[0]
            if game.find('td', {'data-stat': 'game_location'}).contents == ['@']:
                stats['game_location'] = 'A'
            elif game.find('td', {'data-stat': 'game_location'}).contents == ['N']:
                stats['game_location'] = 'N'
            else:
                stats['game_location'] = 'H'
            stats['opponent'] = game.find('td', {'data-stat': 'opp'}).contents[0].contents[0]
            result = game.find('td', {'data-stat': 'game_result'}).contents[0].contents[0]
            stats['game_won'] = (result.split(' ')[0] == 'W')
            stats['player_team_score'] = result.split(' ')[1].split('-')[0]
            stats['opponent_score'] = result.split(' ')[1].split('-')[1]

            # Collect passing stats
            pass_attempts = game.find('td', {'data-stat': 'pass_cmp'})
            if pass_attempts is not None and len(pass_attempts) > 0:
                stats['passing_attempts'] = int(pass_attempts.contents[0])

            pass_completions = game.find('td', {'data-stat': 'pass_att'})
            if pass_completions is not None and len(pass_completions) > 0:
                stats['passing_completions'] = int(pass_completions.contents[0])

            pass_yards = game.find('td', {'data-stat': 'pass_yds'})
            if pass_yards is not None and len(pass_yards) > 0:
                stats['passing_yards'] = int(pass_yards.contents[0])

            pass_touchdowns = game.find('td', {'data-stat': 'pass_td'})
            if pass_touchdowns is not None and len(pass_touchdowns) > 0:
                stats['passing_touchdowns'] = int(pass_touchdowns.contents[0])

            pass_interceptions = game.find('td', {'data-stat': 'pass_int'})
            if pass_interceptions is not None and len(pass_interceptions) > 0:
                stats['passing_interceptions'] = int(pass_interceptions.contents[0])

            pass_rating = game.find('td', {'data-stat': 'pass_rating'})
            if pass_rating is not None and len(pass_rating) > 0:
                stats['passing_rating'] = float(pass_rating.contents[0])

            pass_sacks = game.find('td', {'data-stat': 'pass_sacked'})
            if pass_sacks is not None and len(pass_sacks) > 0:
                stats['passing_sacks'] = int(pass_sacks.contents[0])

            pass_sacks_yards_lost = game.find('td', {'data-stat': 'pass_sacked_yds'})
            if pass_sacks_yards_lost is not None and len(pass_sacks_yards_lost) > 0:
                stats['passing_sacks_yards_lost'] = int(pass_sacks_yards_lost.contents[0])

            # Collect rushing stats
            rushing_attempts = game.find('td', {'data-stat': 'rush_att'})
            if rushing_attempts is not None and len(rushing_attempts) > 0:
                stats['rushing_attempts'] = int(rushing_attempts.contents[0])

            rushing_yards = game.find('td', {'data-stat': 'rush_yds'})
            if rushing_yards is not None and len(rushing_yards) > 0:
                stats['rushing_yards'] = int(rushing_yards.contents[0])

            rushing_touchdowns = game.find('td', {'data-stat': 'rush_td'})
            if rushing_touchdowns is not None and len(rushing_touchdowns) > 0:
                stats['rushing_touchdowns'] = int(rushing_touchdowns.contents[0])

            # Collect receiving stats
            receiving_targets = game.find('td', {'data-stat': 'targets'})
            if receiving_targets is not None and len(receiving_targets) > 0:
                stats['receiving_targets'] = int(receiving_targets.contents[0])

            receiving_receptions = game.find('td', {'data-stat': 'rec'})
            if receiving_receptions is not None and len(receiving_receptions) > 0:
                stats['receiving_receptions'] = int(receiving_receptions.contents[0])

            receiving_yards = game.find('td', {'data-stat': 'rec_yds'})
            if receiving_yards is not None and len(receiving_yards) > 0:
                stats['receiving_yards'] = int(receiving_yards.contents[0])

            receiving_touchdowns = game.find('td', {'data-stat': 'rec_td'})
            if receiving_touchdowns is not None and len(receiving_touchdowns) > 0:
                stats['receiving_touchdowns'] = int(receiving_touchdowns.contents[0])

            # Collect kick return stats
            kick_return_attempts = game.find('td', {'data-stat': 'kick_ret'})
            if kick_return_attempts is not None and len(kick_return_attempts) > 0:
                stats['kick_return_attempts'] = int(kick_return_attempts.contents[0])

            kick_return_yards = game.find('td', {'data-stat': 'kick_ret_yds'})
            if kick_return_yards is not None and len(kick_return_yards) > 0:
                stats['kick_return_yards'] = int(kick_return_yards.contents[0])

            kick_return_touchdowns = game.find('td', {'data-stat': 'kick_ret_td'})
            if kick_return_touchdowns is not None and len(kick_return_touchdowns) > 0:
                stats['kick_return_touchdowns'] = int(kick_return_touchdowns.contents[0])

            # Collect punt return stats
            punt_return_attempts = game.find('td', {'data-stat': 'punt_ret'})
            if punt_return_attempts is not None and len(punt_return_attempts) > 0:
                stats['punt_return_attempts'] = int(punt_return_attempts.contents[0])

            punt_return_yards = game.find('td', {'data-stat': 'punt_ret_yds'})
            if punt_return_yards is not None and len(punt_return_yards) > 0:
                stats['punt_return_yards'] = int(punt_return_yards.contents[0])

            punt_return_touchdowns = game.find('td', {'data-stat': 'punt_ret_td'})
            if punt_return_touchdowns is not None and len(punt_return_touchdowns) > 0:
                stats['punt_return_touchdowns'] = int(punt_return_touchdowns.contents[0])

            # Collect defensive stats
            defense_sacks = game.find('td', {'data-stat': 'sacks'})
            if defense_sacks is not None and len(defense_sacks) > 0:
                stats['defense_sacks'] = float(defense_sacks.contents[0])

            defense_tackles = game.find('td', {'data-stat': 'tackles_solo'})
            if defense_tackles is not None and len(defense_tackles) > 0:
                stats['defense_tackles'] = int(defense_tackles.contents[0])

            defense_tackle_assists = game.find('td', {'data-stat': 'tackles_assists'})
            if defense_tackle_assists is not None and len(defense_tackle_assists) > 0:
                stats['defense_tackle_assists'] = int(defense_tackle_assists.contents[0])

            defense_interceptions = game.find('td', {'data-stat': 'def_int'})
            if defense_interceptions is not None and len(defense_interceptions) > 0:
                stats['defense_interceptions'] = int(defense_interceptions.contents[0])

            defense_interception_yards = game.find('td', {'data-stat': 'def_int_yds'})
            if defense_interception_yards is not None and len(defense_interception_yards) > 0:
                stats['defense_interception_yards'] = int(defense_interception_yards.contents[0])

            defense_safeties = game.find('td', {'data-stat': 'safety_md'})
            if defense_safeties is not None and len(defense_safeties) > 0:
                stats['defense_safeties'] = int(defense_safeties.contents[0])

            # Collect kicking stats
            point_after_attemps = game.find('td', {'data-stat': 'xpm'})
            if point_after_attemps is not None and len(point_after_attemps) > 0:
                stats['point_after_attemps'] = int(point_after_attemps.contents[0])

            point_after_makes = game.find('td', {'data-stat': 'xpa'})
            if point_after_makes is not None and len(point_after_makes) > 0:
                stats['point_after_makes'] = int(point_after_makes.contents[0])

            field_goal_attempts = game.find('td', {'data-stat': 'fga'})
            if field_goal_attempts is not None and len(field_goal_attempts) > 0:
                stats['field_goal_attempts'] = int(field_goal_attempts.contents[0])

            field_goal_makes = game.find('td', {'data-stat': 'fgm'})
            if field_goal_makes is not None and len(field_goal_makes) > 0:
                stats['field_goal_makes'] = int(field_goal_makes.contents[0])

            # Collect punting stats
            punting_attempts = game.find('td', {'data-stat': 'punt'})
            if punting_attempts is not None and len(punting_attempts) > 0:
                stats['punting_attempts'] = int(punting_attempts.contents[0])

            punting_yards = game.find('td', {'data-stat': 'punt_yds'})
            if punting_yards is not None and len(punting_yards) > 0:
                stats['punting_yards'] = int(punting_yards.contents[0])

            punting_blocked = game.find('td', {'data-stat': 'punt_blocked'})
            if punting_blocked is not None and len(punting_blocked) > 0:
                stats['punting_blocked'] = int(punting_blocked.contents[0])

            self.game_stats.append(stats)

    @staticmethod
    def make_player_game_stats(player_id, year):
        """Factory method to return possible stats to collect for a player in a game

            Args:
                - player_id (int): unique Id for the player
                - year (int): The year the stats are for

            Returns:
                - game_stats (dict): dictionary with game stats initialized
        """
        return {
            'player_id': player_id,
            'year': year,
            # General stats
            'game_id': None,
            'date': None,
            'game_number': None,
            'age': None,
            'team': None,
            'game_location': None,
            'opponent': None,
            'game_won': None,
            'player_team_score': 0,
            'opponent_score': 0,
            # Passing stats
            'passing_attempts': 0,
            'passing_completions': 0,
            'passing_yards': 0,
            'passing_rating': 0,
            'passing_touchdowns': 0,
            'passing_interceptions': 0,
            'passing_sacks': 0,
            'passing_sacks_yards_lost': 0,
            # Rushing stats
            'rushing_attempts': 0,
            'rushing_yards': 0,
            'rushing_touchdowns': 0,
            # Receiving stats
            'receiving_targets': 0,
            'receiving_receptions': 0,
            'receiving_yards': 0,
            'receiving_touchdowns': 0,
            # Kick return stats
            'kick_return_attempts': 0,
            'kick_return_yards': 0,
            'kick_return_touchdowns': 0,
            # PUnt return stats
            'punt_return_attempts': 0,
            'punt_return_yards': 0,
            'punt_return_touchdowns': 0,
            # Defense
            'defense_sacks': 0,
            'defense_tackles': 0,
            'defense_tackle_assists': 0,
            'defense_interceptions': 0,
            'defense_interception_yards': 0,
            'defense_interception_touchdowns': 0,
            'defense_safeties': 0,
            # Kicking
            'point_after_attemps': 0,
            'point_after_makes': 0,
            'field_goal_attempts': 0,
            'field_goal_makes': 0,
            # Punting
            'punting_attempts': 0,
            'punting_yards': 0,
            'punting_blocked': 0
        }

    def get_seasons_with_stats(self, profile_soup):
        """Scrape a list of seasons that has stats for the player

            Args:
                - profile_soup (obj): The BeautifulSoup object for the player profile page

            Returns:
                - seasons (dict[]): List of dictionaries with meta information about season stats
        """
        seasons = []
        gamelog_list = profile_soup.find('div', {'id': 'inner_nav'}).find_all('li')[1].find_all('li')
        if len(gamelog_list) > 0 and gamelog_list[0].contents[0].contents[0] == 'Career':
            for season in gamelog_list:
                seasons.append({
                    'year': season.contents[0].contents[0],
                    'gamelog_url': BASE_URL.format(season.contents[0]['href'])
                })
        return seasons


if __name__ == '__main__':
    letters_to_scrape = list(string.ascii_uppercase)
    nfl_scraper = Scraper(letters_to_scrape=letters_to_scrape, num_jobs=10, clear_old_data=False)

    nfl_scraper.scrape_site()
