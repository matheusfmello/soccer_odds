from datetime import date
import pandas as pd
import numpy as np

class PrepareDf:

    def __init__(self, matches, playerRefs, playerAttributes):

        self.matches = matches[matches['homePlayer1'].notnull()].reset_index(drop=True)
        self.matches.sort_values(by='date', inplace=True)
        self.matches.reset_index(drop=True, inplace=True)
        self.matches['fifaGame'] = [self._get_fifa_game(date) for date in self.matches['date']]

        self.playerRefs = playerRefs.drop(['club', 'Name'], axis=1)

        self.playerAttributes = playerAttributes
        self.attributes = self.playerAttributes.columns[1:]
        self.matchStats = self.matches.filter(regex='^(home|away)[^P]').columns

        self.playersMerge = pd.merge(self.playerRefs, self.playerAttributes, how='left', on='ID').drop_duplicates()

    def get_final_df(self, nGames=5):

        #result = pd.DataFrame(columns=self.attributes.extend(self.matchStats))

        self.attributes = self.matches.apply(lambda row: self._get_match_attributes(row), axis=1)
        self.teamsForms = self.matches.apply(lambda row: self._get_teams_forms(row, nGames), axis=1)
        self.matchesWinners = self.matches.apply(lambda row: self._get_match_winner(row), axis=1)

        self.attributesColumns = self.attributes.columns
        self.formColumns = self.teamsForms.columns

        finalDf = pd.concat([self.attributes, self.teamsForms, self.matchesWinners], axis=1)
        finalDf.rename(columns={'0':'winner'}, inplace=True)

        return finalDf

    

    def _get_teams_forms(self, row, nGames):
        homeTeam = row['homeTeam']
        awayTeam = row['awayTeam']
        index = row.name
        homeStatsColumns = self.matches.filter(regex="((H|h)ome)+[A-Za-z]*$").columns.to_list()
        homeStatsColumns.remove('homeTeam')
        awayStatsColumns = self.matches.filter(regex="((A|a)way)+[A-Za-z]*$").columns.to_list()
        awayStatsColumns.remove('awayTeam')
        homeValues = pd.DataFrame(columns=homeStatsColumns)
        homeValues.loc[0] = [np.nan for column in homeValues.columns]
        
        awayValues = pd.DataFrame(columns=awayStatsColumns)
        awayValues.loc[0] = [np.nan for column in awayValues.columns]
        
        shortDf = self.matches.iloc[0:index,]
        homeMatchesDf = shortDf[(shortDf['homeTeam'] == homeTeam) | (shortDf['awayTeam'] == homeTeam)]
        homeMatchesDf = homeMatchesDf.iloc[-nGames:,]
        awayMatchesDf = shortDf[(shortDf['homeTeam'] == awayTeam) | (shortDf['awayTeam'] == awayTeam)]
        awayMatchesDf = awayMatchesDf.iloc[-nGames:,]
        if len(homeMatchesDf) == 0:
            return pd.concat([homeValues, awayValues], axis=1).iloc[0]
        if len(awayMatchesDf) == 0:
            return pd.concat([homeValues, awayValues], axis=1).iloc[0]
        
        homeValues = pd.DataFrame(columns=homeStatsColumns)
        awayValues = pd.DataFrame(columns=awayStatsColumns)
        
        for i in range(nGames):
            if i < len(homeMatchesDf):
                if homeMatchesDf.iloc[i]["homeTeam"] == homeTeam:
                    homeValues.loc[i] = homeMatchesDf.iloc[i][homeStatsColumns].values
                else:
                    homeValues.loc[i] = homeMatchesDf.iloc[i][awayStatsColumns].values
            if i < len(awayMatchesDf):
                if awayMatchesDf.iloc[i]["homeTeam"] == awayTeam:
                    awayValues.loc[i] = awayMatchesDf.iloc[i][homeStatsColumns].values
                else:
                    awayValues.loc[i] = awayMatchesDf.iloc[i][awayStatsColumns].values
        
        homeValues = homeValues.mean(axis=0)
        awayValues = awayValues.mean(axis=0)
        """print(homeValues)
        print('CONCAT')
        print(pd.concat([homeValues, awayValues], axis=0).iloc[0])"""
        form = pd.concat([homeValues, awayValues], axis=0)
        

        return form

        

    def _get_match_attributes(self, row):

        matchAttributes = []

        lineColumns = self.playersMerge.filter(regex='^(?![GK ])').columns[5:].to_list()
        gkColumns = self.playersMerge.filter(regex='^GK ').columns.to_list()
        columns = lineColumns + gkColumns

        homeGK = row[0]
        homePlayers = row[1:11].values
        awayGK = row[11]
        awayPlayers = row[12:22].values

        fifaGame = row['fifaGame']
        playersMerge = self.playersMerge[self.playersMerge['fifaGame'] == fifaGame].set_index('player', drop=True)

        homeGK = playersMerge.loc[homeGK,:]
        homeGK = homeGK.filter(regex='^GK ')


        homeLine = playersMerge.loc[homePlayers,self.attributes]
        homeLine = homeLine.filter(regex='^(?![GK ])')
        homeLine = homeLine.mean(axis=0)


        awayGK = playersMerge.loc[awayGK,:]
        awayGK = awayGK.filter(regex='^GK ')

        awayLine = playersMerge.loc[awayPlayers,self.attributes]
        awayLine = awayLine.filter(regex='^(?![GK ])')
        awayLine = awayLine.mean(axis=0)

        lineDiff = homeLine - awayLine

        GKDiff = homeGK - awayGK
        
        values = lineDiff.to_list() + GKDiff.to_list()
        matchAttributes = pd.Series(data=values, index=columns)

        return matchAttributes

    def _get_match_winner(self, row):

        if row['scoreHome'] > row['scoreAway']:
            winner = 'home'
        elif row['scoreHome'] == row['scoreAway']:
            winner = 'draw'
        else:
            winner = 'away'
        return pd.Series(data=winner, index=["winner"])

    def _get_fifa_game(self,matchday):
        
        releaseDates = {'FIFA16':date(2015,9,22), 'FIFA17':date(2016,9,27), 'FIFA18':date(2017,9,29), 'FIFA19':date(2018,9,28),
                        'FIFA20':date(2019,9,27), 'FIFA21':date(2020,10,9), 'FIFA22':date(2021,10,1), 'FIFA23':date(2022,9,30)}

        for game in range(23, 16, -1):
            if matchday >= releaseDates[f"FIFA{game}"]:
                break
        return game


