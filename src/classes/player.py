import time

from readData import Data

class player:
    def __init__(self, db, date, playerId):

        self.db = db

        self.date = date
        self.playerId = playerId

        query="""SELECT p1.player_name,  p2.*
        FROM Player AS p1
        LEFT JOIN Player_Attributes AS p2
        ON p1.player_api_id = p2.player_api_id
        WHERE p1.player_api_id = {id}
        AND date > '{date}'
        ORDER BY date DESC LIMIT 1"""
        st = time.time()
        query = query.format(id = self.playerId, date=self.date)
        self.info = self.db.returnQuery(query=query)
        et = time.time()
        print("returnQuery player\n")
        print(et-st)

        floatColumns = [col for col in self.info.columns if self.info[col].dtype == "float64"]
        self.info = self.info[floatColumns]


    def getInfo(self):
        return self.info

        

