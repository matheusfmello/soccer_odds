import pandas as pd
from datetime import datetime
import time

from readData import Data
from team import team

class match():
    """
    Implementation of class match

    This class stores matches info. 'match' objects may have results information, in case it's a training variable. In this case,
    there is a set of methods to deal with this attributes.

    """

    def __init__(self, db, id):

        self.id = id
        self.db=db

        query = """SELECT *
        FROM MATCH
        WHERE match_api_id == {match_id};"""
        matchDF = self.db.returnQuery(query=query.format(match_id=id))

        self.date = pd.to_datetime(matchDF["date"].iloc[0]).strftime('%Y-%m-%d')

        players = [self.date]
        for i in range(1,12):
            players.append(matchDF["home_player_{index}".format(index=i)].iloc[0])
            players.append(matchDF["away_player_{index}".format(index=i)].iloc[0])
        self.teamsInfo = team(homeTeamId = matchDF["home_team_api_id"].iloc[0],
                            awayTeamId = matchDF["away_team_api_id"].iloc[0],
                            db=self.db, playersIds=players).getInfo()

        self._matchResults(matchDF)

        self.info = pd.DataFrame([{"match_api_id":id, "winner":self._getMatchResult(),
        "totalGoals":self.totalGoals, }])

        self.info = pd.concat([self.info, self.teamsInfo], axis=1)


    
    def getInfo(self):
        return self.info

    
    # just a set of ideas, not a real implementation yet
    def _matchResults(self, matchDF):
        self.homeGoals = matchDF["home_team_goal"].iloc[0]
        self.awayGoals = matchDF["away_team_goal"].iloc[0]
        self.totalGoals = self.homeGoals + self.awayGoals
        

    def _getMatchResult(self):
        
        if self.homeGoals > self.awayGoals:
            return "home"
        elif self.homeGoals < self.awayGoals:
            return "away"
        else:
            return "draw"
    



