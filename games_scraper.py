import bs4
from selenium.webdriver import Chrome, ChromeOptions
import sqlite3
import re
from time import sleep
from volume import Volume


class Scraper:

    volume = Volume()
    CURRENT_VOLUME = volume.get_volume()

    WEB_LINKS = {
        "flashscore": "https://www.soccer24.com/"
    }

    def scrape(self):
        # CONNECT THE DATABASE
        connector = sqlite3.connect('games-db')
        cursor = connector.cursor()
        cursor.execute('DROP TABLE IF EXISTS allGames')
        cursor.execute('CREATE TABLE allGames(time TEXT, home_team TEXT, away_team TEXT, '
                       'result TEXT, home_odd REAL, draw_odd REAL, away_odd REAL)')

        # OPEN THE WEBSITE AND GET THE DATA
        options = ChromeOptions()
        options.headless = True
        driver = Chrome(options=options, executable_path='C://Windows/chromedriver.exe')
        driver.get(self.WEB_LINKS["flashscore"])
        sleep(1)
        html = driver.execute_script("return document.documentElement.outerHTML;")
        driver.find_element_by_xpath('/html/body/div[4]/div[1]/div/div[1]/div[2]/div[4]/div[2]/div[1]/div[2]/div[3]/div').click()
        sleep(1)
        html_tomorrow = driver.execute_script("return document.documentElement.outerHTML;")

        # CLOSE THE BROWSER
        driver.close()

        # WORK WITH THE DATA AND GET THE GAMES
        soup = bs4.BeautifulSoup(html, 'html.parser')
        soup2 = bs4.BeautifulSoup(html_tomorrow, 'html.parser')
        matches = soup.find_all(class_=re.compile("event__match"))
        matches_tomorrow = soup2.find_all(class_=re.compile("event__match"))
        all_games = [list(game) for game in matches if 'event__match--scheduled' in str(game)]
        all_games_tomorrow = [list(game) for game in matches_tomorrow if 'event__match--scheduled' in str(game)]
        all_games += all_games_tomorrow
        print(len(all_games))
        # INSERT THE GAMES INTO THE DATABASE
        for game in all_games:
            game = game[1:]
            items = {"time": "", "home": "", "away": "", "home_odd": "",
                     "draw_odd": "", "away_odd": ""}

            for element in game:

                # GET THE START HOUR
                if "event__time" in str(element):
                    pattern = r'(\d+[:]\d{2})'
                    time = re.search(pattern, str(element))
                    items["time"] = time.group()

                # GET THE HOME TEAM
                elif "participant--home" in str(element):
                    pattern = r'\"\>([A-z0-9]+.+)\<\/'
                    home_team = re.search(pattern, str(element))
                    items["home"] = home_team.group(1)

                # GET THE AWAY TEAM
                elif "participant--away" in str(element):
                    pattern = r'\"\>([A-z0-9]+.+)\<\/'
                    away_team = re.search(pattern, str(element))
                    items["away"] = away_team.group(1)

                # GET THE HOME ODD
                elif "o_1" in str(element):
                    pattern = r'\"\>(\d{1,2}\.\d{2})\<\/[s]'
                    try:
                        home_odd = re.search(pattern, str(element))
                        items["home_odd"] = home_odd.group(1)
                    except AttributeError:
                        items["home_odd"] = "1.00"

                # GET THE DRAW ODD
                elif "o_0" in str(element):
                    pattern = r'\"\>(\d{1,2}\.\d{2})\<\/[s]'
                    try:
                        draw_odd = re.search(pattern, str(element))
                        items["draw_odd"] = draw_odd.group(1)
                    except AttributeError:
                        items["draw_odd"] = "1.00"

                # GET THE AWAY ODD
                elif "o_2" in str(element):
                    pattern = r'\"\>(\d{1,2}\.\d{2})\<\/[s]'
                    try:
                        away_odd = re.search(pattern, str(element))
                        items["away_odd"] = away_odd.group(1)
                    except AttributeError:
                        items["away_odd"] = "1.00"

            # INSERT THE GAMES INTO THE DATABASE
            cursor.execute('INSERT INTO allGames(time, home_team, away_team, home_odd, draw_odd, away_odd) '
                           'VALUES (?, ?, ?, ?, ?, ?)', (items["time"], items["home"], items["away"],
                                                         items["home_odd"], items["draw_odd"], items["away_odd"]))
        connector.commit()
        connector.close()


scrp = Scraper()
scrp.scrape()
