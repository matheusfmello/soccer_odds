from lib2to3.pgen2 import driver
from urllib.request import urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup
import ssl

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException

import pandas as pd

class scrapper:
    '''
    scrapper Class is used to scrap data from SofaScore. It contains the following attributes

    driver : the driver used to surf the web


    '''

    def __init__(self, path='D:/chromedriver_win32/chromedriver.exe'):
        self.driver = self.getDriver(path=path)
        self.driver.get("https://www.sofascore.com/")

    def getDriver(self, path='D:/chromedriver_win32/chromedriver.exe'):
        chrome_options = Options()
        #chrome_options.add_argument("--headless")
        return webdriver.Chrome(executable_path=path, options=chrome_options)

    def getPlayerInfo(self, url):
        return

    def getMatchesToday(self):

        
        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/main/div/div[2]/div[2]/div/div[1]/div[3]/label/span")))
        oddsButton = self.driver.find_element(By.XPATH, "/html/body/div[1]/div/main/div/div[2]/div[2]/div/div[1]/div[3]/label/span")
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
            if self._checkExistsByClass('blXay'):
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
        lineups = self._getLineups()

        df = pd.concat([df, lineups], axis=1).iloc[:,:-1]

        return df

    def _getLineups(self):

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
        
            if self._checkExistsByClass("jwanNG") and self.driver.find_element(By.CLASS_NAME, "jwanNG").text == "LINEUPS":
                
                lineupButton = self.driver.find_element(By.CLASS_NAME, "jwanNG")
                lineupButton.click()
                # wait until players are avilable
                WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.CLASS_NAME, "kDQXnl")))
                players = self.driver.find_elements(By.CLASS_NAME, "kDQXnl")
                playerNames=[]
                for player in players:
                    playerNames.append(player.find_elements(By.CLASS_NAME, "sc-eDWCr")[2].accessible_name)
                playerNames = [self._isCaptain(playerName) for playerName in playerNames]
                playerNames.append(nameInPanel)
                

                df.loc[len(df)] = playerNames
            else:
                df.loc[len(df), "homeTeam"] = nameInPanel

        return df
        

    
    def _isCaptain(self, name):
        if name.startswith("(c) "):
            name = name[4:]
        return name

    def _checkExistsByClass(self, className):
        try:
            self.driver.find_element(By.CLASS_NAME, className)
        except NoSuchElementException:
            return False
        return True

    def _staleReferenceCatcher(self, button):
        try:
            button.click()
            return
        except StaleElementReferenceException:
            return self._staleReferenceCatcher(button)
