
from readData import Data
from player import player

import pandas as pd
import time

class team():

    """ Implementation of class team

    this class stores information about the team form, such as last results, ball possession, it's players and so on, if available.

    :float form: team performance in terms of points conquered in last 10 matches - W=3, D=1, L=0
    :float possession: team average ball possession in last 10 matches
    :player players: set of players from the team

    """
    def __init__(self, homeTeamId, awayTeamId, db, playersIds):

        self.db = db

        self.homeTeamId=homeTeamId
        self.awayTeamId=awayTeamId

        self.homePlayers = playersIds[0:12]
        self.awayPlayers = playersIds[12:24]

        #self.name = team["team_long_name"]

        self.date = playersIds.pop(0)
        
        queryPlayers ="""
        SELECT
            *, MAX(date)
        FROM
            PLAYER_ATTRIBUTES
        WHERE
            date < '{date}' AND
            player_api_id IN ({playersIds})
        GROUP BY player_api_id """

        queryPlayers=queryPlayers.format(date=self.date,
                                        playersIds=str(playersIds)[1:-1])
        players = db.returnQuery(query=queryPlayers)


        players["team"] = players["player_api_id"].apply(lambda x: self._getPlayerTeam(x))
        
        self.homePlayers = players[players["team"] == "home"]
        self.awayPlayers = players[players["team"] == "away"]

        floatColumns = [col for col in players.columns if players[col].dtype == "float64"]
        
        self.homePlayers = self.homePlayers[floatColumns].add_prefix("home_")
        self.awayPlayers = self.awayPlayers[floatColumns].add_prefix("away_")


        self.homePlayers = self.homePlayers.mean(axis=0).to_frame().T
        self.awayPlayers = self.awayPlayers.mean(axis=0).to_frame().T

        self.homePlayers["home_form"] = self._getForm(self.homeTeamId)
        self.awayPlayers["away_form"] = self._getForm(self.awayTeamId)

        self.info = pd.concat([self.homePlayers, self.awayPlayers], axis=1).reset_index(drop=True)

    def _getForm(self, teamId):
        query = """
        SELECT 
            date, home_team_api_id, away_team_api_id, home_team_goal, away_team_goal
        FROM MATCH
        WHERE (home_team_api_id == {teamId} OR away_team_api_id == {teamId}) AND date < '{date}'
        ORDER BY date DESC
        LIMIT 10
        """

        query=query.format(teamId=teamId, date=self.date)

        lastMatches = self.db.returnQuery(query=query)

        totalPoints = lastMatches.shape[0] * 3
        if totalPoints == 0:
            totalPoints=1
        pointsEarned = 0

        for i in range(0, lastMatches.shape[0]):
            if lastMatches.loc[i, "home_team_goal"] == lastMatches.loc[i, "away_team_goal"]:
                pointsEarned = pointsEarned + 1
            elif lastMatches.loc[i,"home_team_api_id"] == teamId:
                if lastMatches.loc[i,"home_team_goal"] > lastMatches.loc[i,"away_team_goal"]:
                    pointsEarned = pointsEarned + 3
            else:
                if lastMatches.loc[i,"home_team_goal"] < lastMatches.loc[i,"away_team_goal"]:
                    pointsEarned = pointsEarned + 3
        return pd.DataFrame([{"form" : pointsEarned / totalPoints}])

    def _getPlayerTeam(self, row):
        if row in self.homePlayers:
            result="home"
        else:
            result="away"
        return result

    def getInfo(self):
        return self.info
