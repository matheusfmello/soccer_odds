from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import time


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from http.client import IncompleteRead

import os
import re
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta


class Scrapper:

    """
    Class used to scrap football data

    :param path:            The chrome driver path in your computer. Only used to get today matches information.

    :def get_matches():      Gets past matches information from the leagues chosen in a certain period.
                            Uses beautifulSoup framework

    :def get_matches_today(): Gets predicted lineups and odds about matches to be played today.
                            Uses selenium framework

    :def getPlayersStats(): Gets players stats in FIFA game.

    """

    def __init__(self, path='D:/chromedriver_win32/chromedriver.exe'):

        self.originLink = 'https://fbref.com'
        self.path=path

        self.baseFolder = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.dataFolder = os.path.join(self.baseFolder, 'data')

        self.scoresHome = []
        self.scoresAway = []
        self.homeTeams = []
        self.awayTeams = []
        self.scoresHome = []
        self.scoresAway = []
        self.dates = []
        self.homeXG = []
        self.awayXG = []

    #--------------------           OLD MATCHES FUNCTIONS       -------------------------#
    
    def get_matches(self, leagues = ["Bundesliga", "Premier League", "La Liga", "Ligue 1", "Eredivise"], start=date(2016,1,1), end=date.today()):
        
        """
        This function returns a data frame containing past matches information from fbref.com/
        The web scraping process is unstable, so we store a backup file every 1st day of the month in data/checkPoint.pkl

        :param leagues: A list containing the leagues the user wants to scrap
        :param start: A datetime.date object containing the starting date to scrap
        :param end: A datetime.date object containing the ending date to scrap

        :return: Dataframe containing the information found or nan otherwise
        """

        df = pd.DataFrame(columns=["{team}Player{i}".format(team="home" if i <=10 else "away", i=i+1 if i <=10 else i-10) for i in range(0,22)])
        matchStats = pd.DataFrame(columns=['yellowCardsHome', 'redCardsHome', 'yellowCardsAway', 'redCardsAway',
        "homeFouls", "awayFouls", "homeCorners", "awayCorners", "homeCrosses", "awayCrosses", "homeTouches", "awayTouches",
        "homeTackles", "awayTackles", "homeInterceptions", "awayInterceptions", "homeAerialsWon", "awayAerialsWon",
        "homeClearances", "awayClearances", "homeOffsides", "awayOffsides", "homeGoalKicks", "awayGoalKicks", "homeThrowIns",
        "awayThrowIns", "homeLongBalls", "awayLongBalls"])
        dfMatchStats = pd.concat([df, matchStats], axis=1)

        day = start
        while day != end:

            time.sleep(np.random.randint(10))

            yearNow, monthNow, dayNow = self._get_date(day)
            urlDay = self.originLink + "/en/matches/{year}-{month}-{day}".format(year=yearNow, month=monthNow, day=dayNow)
            print(urlDay)
            html = urlopen(urlDay)
            bs = BeautifulSoup(html.read(), 'html.parser')

            try:

                championshipTables = bs.find_all('div', {'class':'table_wrapper'})
                errorList = []
                for i in range(len(championshipTables)):
                    try:
                        championshipTables[i].find('a', {'href':re.compile('^/en/comps/')}).get_text()
                    except AttributeError:
                        errorList.append(i)
                for error in errorList:
                    del championshipTables[error]
                desiredTables = [ch for ch in championshipTables if ch.find('a', {'href':re.compile('^/en/comps/')}).get_text() in leagues]


                for table in desiredTables:

                    time.sleep(4)

                    matchesLinks = []

                    homeTeams = table.find_all('td', {'data-stat':'home_team'})
                    for team in homeTeams:
                        self.homeTeams.append(team.get_text())
                        self.dates.append(day)

                    awayTeams = table.find_all('td', {'data-stat':'away_team'})
                    for team in awayTeams:
                        self.awayTeams.append(team.get_text())

                    scores = table.find_all('td', {'data-stat':'score'})
                    for score in scores:
                        scoreHome, scoreAway = self._get_score(score.get_text())
                        self.scoresHome.append(scoreHome)
                        self.scoresAway.append(scoreAway)
                        if np.isnan(scoreHome):
                            # random link whose match has no info
                            matchesLinks.append('/en/matches/0a7d1069/Fleetwood-Town-Lincoln-City-April-13-2020-League-One')
                        else:
                            matchesLinks.append(score.find('a', {'href':re.compile('^/')})['href'])

                    if table.find_all('td', {'data-stat':'home_xg'}):
                        homeXG = table.find_all('td', {'data-stat':'home_xg'})
                        awayXG = table.find_all('td', {'data-stat':'away_xg'})
                        for xg in homeXG:
                            self.homeXG.append(xg.get_text())
                        for xg in awayXG:
                            self.awayXG.append(xg.get_text())
                    else:
                        for team in homeTeams:
                            self.homeXG.append(np.nan)
                            self.awayXG.append(np.nan)

                    for link in matchesLinks:
                        dfMatchStats.loc[len(dfMatchStats)] = self._get_match_stats(link)

            except NoSuchElementException:
                pass
            
            if day.day == 1:
                # if the process crashes, we have a checkpoint every month starter
                dfCheckpoint = dfMatchStats.copy()
                dfCheckpoint["homeTeam"] = self.homeTeams
                dfCheckpoint["awayTeam"] = self.awayTeams
                dfCheckpoint["scoreHome"] = self.scoresHome
                dfCheckpoint["scoreAway"] = self.scoresAway
                dfCheckpoint["homeXG"] = self.homeXG
                dfCheckpoint["awayXG"] = self.awayXG
                dfCheckpoint["date"] = self.dates
                dfCheckpoint.to_pickle(os.path.join(self.dataFolder, 'checkPoint.pkl'))

            day = day + timedelta(days=1)

        dfMatchStats["homeTeam"] = self.homeTeams
        dfMatchStats["awayTeam"] = self.awayTeams
        dfMatchStats["scoreHome"] = self.scoresHome
        dfMatchStats["scoreAway"] = self.scoresAway
        dfMatchStats["homeXG"] = self.homeXG
        dfMatchStats["awayXG"] = self.awayXG
        dfMatchStats["date"] = self.dates

        return dfMatchStats

    def _get_match_stats(self, url):

        """
        Helper function to extract the match stats for each match in get_matches()

        :param url: The match report url - is extracted in get_matches()

        :return: List with match stats

        """

        stats={"Fouls":[np.nan, np.nan], "Corners":[np.nan, np.nan], "Crosses":[np.nan, np.nan], "Touches":[np.nan, np.nan],
        "Tackles":[np.nan, np.nan], "Interceptions":[np.nan, np.nan],"Aerials Won":[np.nan, np.nan],
        "Clearances":[np.nan, np.nan], "Offsides":[np.nan, np.nan], "Goal Kicks":[np.nan, np.nan], "Throw Ins":[np.nan, np.nan],
        "Long Balls":[np.nan, np.nan]}

        matchStatsList = []
        htmlMatch = urlopen(self.originLink + url)
        bsMatch = BeautifulSoup(htmlMatch.read(), 'html.parser')
        homeLineup = bsMatch.find('div', {'class':'lineup', 'id':'a'})
        if not homeLineup:
            homePlayers = []
            awayPlayers = []
            for i in range(0,11):
                homePlayers.append(np.nan)
                awayPlayers.append(np.nan)
            yellowCardsHome = np.nan
            redCardsHome = np.nan
            yellowCardsAway = np.nan
            redCardsAway = np.nan
            matchStatsList.extend([yellowCardsHome, redCardsHome, yellowCardsAway, redCardsAway])
            for key, value in stats.items():
                matchStatsList.extend(value)
            return homePlayers + awayPlayers + matchStatsList
        homePlayers = homeLineup.find_all('a', {'href':re.compile('^/en/players')})[0:11]
        homePlayers = [player.get_text() for player in homePlayers]
        awayLineup = bsMatch.find('div', {'class':'lineup', 'id':'b'})
        awayPlayers = awayLineup.find_all('a', {'href':re.compile('^/en/players')})[0:11]
        awayPlayers = [player.get_text() for player in awayPlayers]
        matchCards = bsMatch.find_all('div', {'class':'cards'})
        yellowCardsHome = len(matchCards[0].find_all('span', {'class':'yellow_card'})) + len(matchCards[0].find_all('span', {'class':'yellow_red_card'}))
        redCardsHome = len(matchCards[0].find_all('span', {'class':'red_card'})) + len(matchCards[0].find_all('span', {'class':'yellow_red_card'}))
        yellowCardsAway = len(matchCards[1].find_all('span', {'class':'yellow_card'})) + len(matchCards[1].find_all('span', {'class':'yellow_red_card'}))
        redCardsAway = len(matchCards[1].find_all('span', {'class':'red_card'})) + len(matchCards[1].find_all('span', {'class':'yellow_red_card'}))
        matchStatsList.extend([yellowCardsHome, redCardsHome, yellowCardsAway, redCardsAway])
        

        extraStatsPanel = bsMatch.find("div", {"id":"team_stats_extra"})
        for statColumn in extraStatsPanel.find_all("div", recursive=False):
            column = statColumn.find_all("div")
            columnValues = [value.get_text() for value in column]
            for index, value in enumerate(columnValues):
                if not value.isdigit() and value in stats:
                    try:
                        stats[value] = [int(columnValues[index-1]), int(columnValues[index+1])]
                    except ValueError:
                        stats[value] = [int(columnValues[index-1]) if columnValues[index-1].isdigit() else np.nan, int(columnValues[index+1]) if columnValues[index+1].isdigit() else np.nan]
        for key, value in stats.items():
            matchStatsList.extend(value)
        
        return homePlayers + awayPlayers + matchStatsList



    def _get_date(self, date):

        """
        Helper function used to format url in the desired date in get_matches()

        :param date: datetime.date object
        :return: The formatted year, month and day of the date object

        """

        year = str(date.year)
        month = str(date.month) if date.month >= 10 else '0' + str(date.month)
        day = str(date.day) if date.day >= 10 else '0' + str(date.day)
        return year, month, day
        
    def _get_score(self, score):
        
        """
        Helper function to format the extracted score of each match

        :param score: The score extracted from the website
        :return: Scores for home and away teams formatted
        """
        try:
            score = str(score)
            scores = score.split('–')
            scoreHome = int(scores[0])
            scoreAway = int(scores[1])
        except:
            scoreHome = np.nan
            scoreAway = np.nan
        return scoreHome, scoreAway
    
    
    

    #--------------------           TODAY MATCHES FUNCTIONS       -------------------------#   

    def _get_driver(self, path='D:/chromedriver_win32/chromedriver.exe'):
        chrome_options = Options()
        return webdriver.Chrome(executable_path=path, options=chrome_options)  

    def get_matches_today(self):

        self.driver = self._get_driver(path=self.path)
        self.driver.get("https://www.sofascore.com/")
        
        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, "slider")))
        oddsButton = self.driver.find_element(By.CLASS_NAME, "slider")
        oddsButton.click()

        homeTeam=[]
        awayTeam=[]
        odds=[]
        homeOdds = []
        drawOdds = []
        awayOdds = []

        WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.CLASS_NAME, 'fvgWCd')))

        matches = self.driver.find_elements(By.CLASS_NAME, 'js-list-cell-target')
        for match in matches:
            if self._check_exists_by_class('blXay'):
                homeTeam.append(match.find_element(By.CLASS_NAME, 'blXay').text)
                awayTeam.append(match.find_element(By.CLASS_NAME, 'crsngN').text)

                if match.find_element(By.CLASS_NAME, 'haEAMa').text == '-':
                    oddsObject = match.find_elements(By.CLASS_NAME, 'fvgWCd')
                    for odd in oddsObject:
                        odds.append(odd.text)

        while(len(odds) > 0):
            homeOdds.append(odds.pop(0))
            drawOdds.append(odds.pop(0))
            awayOdds.append(odds.pop(0))

        df = pd.DataFrame({"homeTeam":homeTeam, "awayTeam":awayTeam, "homeOdds":homeOdds, "drawOdds":drawOdds, "awayOdds":awayOdds})
        lineups = self._get_lineups()

        df = pd.concat([df, lineups], axis=1).iloc[:,:-1]

        return df

    def _get_lineups(self):

        matches = self.driver.find_elements(By.CLASS_NAME, "kusmLq")

        nameInPanel = ""

        df = pd.DataFrame(columns=["{team}Player{i}".format(team="home" if i <=10 else "away", i=i+1 if i <=10 else i-10) for i in range(0,22)])
        df["homeTeam"] = []

        for match in matches:

            self.driver.execute_script("arguments[0].click()", match)

            #wait until panel is refreshed

            waiter = WebDriverWait(driver=self.driver, timeout=10, poll_frequency=1)
            waiter.until(lambda drv: drv.find_element(By.CLASS_NAME, "dsMMht").text != nameInPanel)
            nameInPanel = self.driver.find_element(By.CLASS_NAME, "dsMMht").text
        
            if self._check_exists_by_class("jwanNG") and self.driver.find_element(By.CLASS_NAME, "jwanNG").text == "LINEUPS":
                
                lineupButton = self.driver.find_element(By.CLASS_NAME, "jwanNG")
                lineupButton.click()
                # wait until players are avilable
                WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.CLASS_NAME, "kDQXnl")))
                players = self.driver.find_elements(By.CLASS_NAME, "kDQXnl")
                playerNames=[]
                for player in players:
                    playerNames.append(player.find_elements(By.CLASS_NAME, "sc-eDWCr")[2].accessible_name)
                playerNames = [self._is_captain(playerName) for playerName in playerNames]
                playerNames.append(nameInPanel)
                

                df.loc[len(df)] = playerNames
            else:
                df.loc[len(df), "homeTeam"] = nameInPanel

        return df
        

    
    def _is_captain(self, name):
        if name.startswith("(c) "):
            name = name[4:]
        return name

    def _check_exists_by_class(self, className):
        try:
            self.driver.find_element(By.CLASS_NAME, className)
        except NoSuchElementException:
            return False
        return True

    def _stale_reference_catcher(self, button):
        try:
            button.click()
            return
        except StaleElementReferenceException:
            return self._stale_reference_catcher(button)

    #--------------------      PLAYERS REFS  FUNCTIONS       -------------------------#

    def get_players_refs(self, leagues = ["Bundesliga", "Premier League", "La Liga", "Ligue 1", "Eredivise"], years = [17, 18, 19, 20, 21, 22, 23]):

        baseURL = "https://sofifa.com/players?type=all"
        leaguesIds = {"Bundesliga":"&lg%5B%5D=19", "Premier League":"&lg%5B%5D=13", "La Liga":"&lg%5B%5D=53",
                     "Ligue 1":"&lg%5B%5D=16", "Eredivise":"&lg%5B%5D=10"} # filters embedded in the url

        years = [str(year) for year in years]
        yearsIds = {'17':'&r=170099&set=true', '18':'&r=180084&set=true', '19':'&r=190075&set=true', '20':'&r=200061&set=true',
        '21':'&r=210064&set=true', '22':'&r=220069&set=true', '23':'&r=230008&set=true'}


        filters = ''.join([leaguesIds[league] for league in leagues])

        playersDf = pd.DataFrame(columns=["ID", 'FIFA', "Name", "Club"])

        for year in years:

            url = baseURL + filters + yearsIds[year] + "&offset=00" # offset allows us to navigate between pages


            req = Request(url , headers={'User-Agent': 'Mozilla/5.0'})

            html = urlopen(req).read()
    
            bs = BeautifulSoup(html, "html.parser")

            firstPlayer = bs.find('td', {'class':'col-name'}).find('a', {'href':re.compile('^/player/')})['href'] # save first player in search
            newTopPlayer = ''
            lastTopPlayer = ' '
            


            while newTopPlayer != firstPlayer and newTopPlayer != lastTopPlayer:

                allPlayers = bs.find_all('td', {'class':'col-name'})
                playersIds = [self._checkColName(player, 'href') for player in allPlayers]
                playersIds = [id for id in playersIds if id is not None]

                playersNames = [self._checkColName(player, 'aria-label') for player in allPlayers]
                playersNames = [name for name in playersNames if name is not None]

                clubsNames = [self._check_player_club(player) for player in allPlayers]
                clubsNames = [club for club in clubsNames if club is not None]

                pageInfo = pd.DataFrame({"ID":playersIds, 'FIFA':year, "Name":playersNames, "Club":clubsNames})

                playersDf = pd.concat([playersDf, pageInfo], axis=0)

                lastTopPlayer = newTopPlayer
                url, req, html, bs, newTopPlayer = self._get_next_page(url)
        
            playersDf = playersDf.iloc[:-60,:]

            print(f"FIFA {year} PLAYERS EXTRACTED \n\n\n")

        playersDf.reset_index(drop=True).drop_duplicates().reset_index(drop=True)

        

        return playersDf
        

    def _get_next_page(self, url):
        pattern = re.compile(r" ?\d+$") # gets last digits occurrance in url
        offsetNum = pattern.search(url).group()
        url = self._rreplace(url, offsetNum, str(int(offsetNum) + 60)) # next page adds 60 to url code. we replace it to navigate in pages
        req = Request(url , headers={'User-Agent': 'Mozilla/5.0'})
        html = urlopen(req).read()
        bs = BeautifulSoup(html, "html.parser")
        newTopPlayer = bs.find('td', {'class':'col-name'}).find('a', {'href':re.compile('^/player/')})['href']

        return url, req, html, bs, newTopPlayer
    
    def _rreplace(self, string, oldPattern, newPattern):
        return newPattern.join(string.rsplit(oldPattern, 1))

    def _checkColName(self, soup, attribute):
        try:
            return soup.find('a', {'href':re.compile('^/player/')})[attribute]
        except TypeError:
            return

    def _check_player_club(self, soup):
        try:
            return soup.find('a', {'href':re.compile('^/team/')}).get_text()
        except AttributeError:
            return

    #--------------------      PLAYERS ATTRIBUTES  FUNCTIONS       -------------------------#

    def get_players_attributes(self, playersIds, checkPoint = None):

        """
        This function returns a data frame containing the ids found in the df input playersRefs and the attributes linked
        to that id.

        :param playersIds: A list containing the players ids the user want so scrape.

        :checkPoint: An optional df containing previous partial results from this function.

        :return: Dataframe containing the ids and the attributes of the referred player
        """

        baseUrl = "https://sofifa.com/"
        playersIds = playersIds.unique()

        columns = ['ID', 'Crossing', 'Finishing', 'Heading Accuracy', 'Short Passing', 'Volleys', 'Dribbling', 'Curve',
        'FK Accuracy', 'Long Passing', 'Ball Control', 'Acceleration', 'Sprint Speed', 'Agility', 'Reactions',
        'Balance', 'Shot Power', 'Jumping', 'Stamina', 'Strength', 'Long Shots', 'Aggression', 'Interceptions',
        'Positioning', 'Vision', 'Penalties', 'Composure', 'Marking', 'Standing Tackle', 'Sliding Tackle',
        'GK Diving', 'GK Handling', 'GK Kicking', 'GK Positioning', 'GK Reflexes']

        result = pd.DataFrame(columns=columns)

        if checkPoint is not None:
            start=len(checkPoint)
        else:
            start=0

        for id in playersIds[start:len(playersIds)]:
            
            try:
                url = f"{baseUrl}{id}?attr=classic"
                req = Request(url , headers={'User-Agent': 'Mozilla/5.0'})
                html = urlopen(req).read()
                bs = BeautifulSoup(html, "html.parser")

                attributesBoxes = bs.find_all('div', {'class':'col col-12'})[1].find_all('span', {'class':'bp3-tag'})
                result.loc[len(result)] = [id] + [int(box.get_text()) for box in attributesBoxes]

            except Exception as e:
                checkPoint = pd.concat([checkPoint, result], axis=0)
                newLen = len(checkPoint)
                print(e)
                print(f'A checkpoint dataframe was returned due to the above error. It now contains {newLen} rows.')
                return checkPoint

        return result
