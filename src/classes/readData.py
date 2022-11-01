import sys
import os

import pandas as pd

import sqlite3


class Data:

    """Implementation of class Data

    - this class auxiliates the user to return SQL queries and prepares datasets for usage.
    """

    def __init__(self, dbPath=None):

        if dbPath is None:

            baseFolder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            dataFolder = os.path.join(baseFolder, 'data')
            self.dbPath = os.path.join(dataFolder, "database.sqlite")
        else:
            self.dbPath=dbPath

        self.conn = sqlite3.connect(self.dbPath)

        self._prepared = False

        self._validateData()

        if not self._prepared:
            self._prepareData()

            

    def getDataset(self):

        """this process involves getting aggregated information about players and teams involved in the match"""
        rawMatches = self.returnQuery("match")
        cleanMatches = self._cleanMatches(rawMatches)
        

    
        

    def returnQuery(self, table=None, query=None):
        
        if table is not None:
                query="""SELECT *
                FROM {table}"""
                query = query.format(table=table)
        else:
            query=query

        table = pd.read_sql(query, self.conn)
        
        return table

    def close(self):
        self.conn.close()

    #### Auxiliary Functions #######

    # Database related functions

    def _validateData(self):

        dateTables = self.conn.cursor().execute("""SELECT m.name
        FROM sqlite_master m
        WHERE m.type = 'table' AND EXISTS 
        (SELECT 1 FROM pragma_table_info(m.name) m1 where m1.name = 'date')""").fetchall()

        dateTableNames = [dateTables[i][0] for i in range(0, len(dateTables))]

        for tableName in dateTableNames:
            query = """SELECT *
            FROM {table}
            LIMIT 2""".format(table=tableName)
            table = pd.read_sql(query, self.conn)
            if table["date"].dtype != '<M8[ns]':
                return
        self._prepared = True

    def _prepareData(self):

        print("Your data is being prepared...\n")
        
        # let's get tables which contains 'date' column
        dateTables = self.conn.cursor().execute("""SELECT m.name
        FROM sqlite_master m
        WHERE m.type = 'table' AND EXISTS 
        (SELECT 1 FROM pragma_table_info(m.name) m1 where m1.name = 'date')""").fetchall()

        dateTableNames = [dateTables[i][0] for i in range(0, len(dateTables))]

        for tableName in dateTableNames:
            print("Preparing {table} table\n".format(table=tableName))
            query = """SELECT *
            FROM {table}""".format(table=tableName)
            table = pd.read_sql(query, self.conn)
            table["date"] = pd.to_datetime(table["date"], format="%Y-%m-%d")
            table.to_sql(tableName, self.conn, if_exists="replace", index=False)
        
        self._onlyAvailablePlayers()
            
        print("Done! Tables are ready to use")
        self._prepared = True
    
    def _onlyAvailablePlayers(self):
        print("Filtering only available players...")
        matchesDF = pd.read_sql("SELECT * FROM MATCH", self.conn)
        places=["home", "away"]
        playersCols = ["{status}_player_{num}".format(status=place, num=i) for place in places for i in range(1,12)]
        matchesDF = matchesDF[matchesDF[playersCols].notnull().all(1)].reset_index(drop=True)
        matchesDF.to_sql("Match", self.conn, if_exists="replace", index=False)

    #def _cleanMatches(self, rawMatches):
    
            

            
