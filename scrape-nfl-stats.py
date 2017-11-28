import requests
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool
import time
import shutil
import re

BASE_URL = 'https://www.pro-football-reference.com{0}'
PLAYER_LIST_URL = 'https://www.pro-football-reference.com/players/{0}'
PLAYER_PROFILE_URL = 'https://www.pro-football-reference.com/players/{0}/{1}'
PLAYER_GAMELOG_URL = 'https://www.pro-football-reference.com/players/{0}/{1}/gamelog/{2}'

HEADERS = {
    'user-agent': ('Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36')
}

DATA_DIR = 'data'

class Scraper():
    """Scraper for pro-football-reference.com to collect NFL player stats"""

    def __init__(self, letters_to_scrape=['A'], num_jobs=1, clear_old_data=True):
        """Initialize the scraper to get player stats

                Args:
                    - letters_to_scrape (str[]): The site sorts players by the first letter of their
                      last name. This array tells the scraper which letters to scrape data for.
                    - num_jobs (int): Number of concurrent jobs the scraper should run. While Python
                      can't multi-thread, it can manage multiple processes at once, which allows it to
                      utilize time spent waiting for the server to respond.
                    - clear_old_data (boolean): Whether or not the data file should be wiped before
                      starting the scrape.

                Returns:
                    None
        """
        self.letters_to_scrape = [letter.upper() for letter in letters_to_scrape]
        self.num_jobs = num_jobs
        self.clear_old_data = clear_old_data
        self.session = requests.Session()
        self.start_time = time.time()
        self.cross_process_player_count = 0

        if num_jobs > 1:
            self.multiprocessing = True
            self.worker_pool = Pool(num_jobs)
        else:
            self.multiprocessing = False

    def scrape_site(self):
        """Pool workers to scrape players by first letter of last name"""
        if self.clear_old_data:
            self.clear_data_dir()
        for letter in self.letters_to_scrape:
            player_profile_urls = self.get_players_for_letter(letter)
            for player_profile_url in player_profile_urls:
                player = Player(player_profile_url, self)
                player.scrape_profile()

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
        except:
            retry_count += 1
            if retry_count <= 3:
                self.session = requests.Session()
                return self.get_page(url, retry_count)
            else:
                raise

    def clear_data_dir(self):
        """Clears the scraped data"""
        try:
            shutil.rmtree(DATA_DIR)
        except FileNotFoundError:
            pass


class Player():
    """An NFL player"""

    def __init__(self, profile_url, scraper):
        """
            Args:
                - profile_url (str): URL to the player's profile
                - scraper (obj): instance of Scraper class

            Returns:
                None
        """
        self.profile_url = profile_url
        self.scraper = scraper
        self.profile = {
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

        profile_attributes = profile_section.find_all('p')
        current_attribute = 1
        num_attributes = len(profile_attributes)

        self.profile['position'] = profile_attributes[current_attribute].contents[2].split('\n')[0].split(' ')[1]
        current_attribute += 1

        self.profile['height'] = profile_attributes[current_attribute].find('span', {'itemprop': 'height'}).contents[0]
        self.profile['weight'] = profile_attributes[current_attribute].find('span', {'itemprop': 'weight'}).contents[0].split('lb')[0]
        current_attribute += 1

        affiliation_section = profile_section.find('span', {'itemprop': 'affiliation'})
        if affiliation_section is not None:
            self.profile['current_team'] = affiliation_section.contents[0].contents[0]
            current_attribute += 1

        self.profile['birth_date'] = profile_attributes[current_attribute].find('span', {'itemprop': 'birthDate'})['data-birth']
        birth_place_section = profile_attributes[current_attribute].find('span', {'itemprop': 'birthPlace'}).contents
        self.profile['birth_place'] = re.split('\xa0', birth_place_section[0])[1] + ' ' + birth_place_section[1].contents[0]
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

    def scrape_season_gamelog(self, gamelog_url):
        """Scrape player stats for a given year

            Args:
                - gamelog_url (str): URL to the stats for a given year

            Returns:
                - stats (dict): All of the player's stats for that year
        """
        response = self.scraper.get_page(self.profile_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        stats_table = soup.find('table', {'id': 'stats'})

    @staticmethod
    def make_player_game_stats():
        """Factory method to return possible stats to collect for a player in a game

            Returns:
                - game_stats (dict): dictionary with game stats initialized
        """
        return {
            # General stats
            'date': None,
            'game_number': None,
            'age': None,
            'team': None,
            'game_at_home': None,
            'opponent': None,
            'game_won': None,
            'player_team_score': 0,
            'opponent_score': 0,
            # Passing stats
            'passing_attempts': 0,
            'passing_completions': 0,
            'passing_yards': 0,
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
            'kick_return_touchdowns': 0
            # Defense
            'defense_sacks': 0,
            'defense_tackles': 0,
            'defense_tackle_assists': 0,
            'defense_interceptions': 0,
            'defense_interception_yards': 0,
            'defense_interception_touchdowns': 0,
            # Fumbles
            'forced_fumbles': 0,
            'fumbles': 0,
            'fumble_recoveries': 0,
            'fumble_recovery_yards': 0,
            'fumble_recovery_touchdowns': 0,
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
                    'gamelog_link': BASE_URL.format(season.contents[0]['href'])
                })
        return seasons



if __name__ == '__main__':
    letters_to_scrape = ['A']
    nfl_scraper = Scraper(letters_to_scrape=letters_to_scrape, num_jobs=1, clear_old_data=False)

    nfl_scraper.scrape_site()
