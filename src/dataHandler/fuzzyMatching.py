
import pandas as pd
import numpy as np
from datetime import datetime, date
from rapidfuzz import process, fuzz

class FuzzyMatcher:

    def __init__(self, playersDf, matchesDf):
        
        self.players = playersDf
        self.players['FIFA'] = [int(game) for game in self.players['FIFA']]
        self.matches = matchesDf

    #--------------------      PLAYERS ATTRIBUTES  FUNCTIONS       -------------------------#

    def fuzzy_match(self):

        playersPrepared = self._prepare_players_from_matches()

        merge = playersPrepared.merge(self.players, left_on=["player", "fifaGame"], right_on=["Name","FIFA"], how="left")
        merge = merge[merge['player'].notna()].reset_index(drop=True)
        mergeNoMatches = merge[merge["ID"].isnull()].reset_index(drop=True)

        # for each player, fill game and url with last info available, if available at all
        for player in mergeNoMatches['player'].unique():
            merge[merge['player'] == player] = merge[merge['player'] == player].fillna(method='ffill')

        # update mergeNoMatches
        mergeNoMatches = merge[merge["ID"].isnull()].reset_index(drop=True)
        perfectMatches = merge[merge['ID'].notna()].reset_index(drop=True)

        """namesMergeNoMatches = mergeNoMatches['player'].unique()
        namesPlayersRefsNoMatches = np.unique([player for player in self.players['Name'] if player not in perfectMatches['Name']])"""

        
        fuzzyResult = pd.DataFrame(columns=['player', 'Name', 'FIFA'])

        # extract the most similar names to those in mergeNoMatches, and their scores
        for fifa in mergeNoMatches['fifaGame'].unique():
            
            fuzzyTuples = []
            playersPairsChosen = {}

            names = mergeNoMatches[mergeNoMatches['fifaGame'] == fifa]['player'].unique()
            namesRefs = self.players[self.players['FIFA'] == fifa]['Name'].unique()

            fuzzyTuples = ([process.extract(name, namesRefs, limit=3) for name in names])

        # choice is made after adding club information to the score given by rapidfuzz
             
            for playerRef, listOfTuples in enumerate(fuzzyTuples):
                clubsPlayerMerge = np.unique(mergeNoMatches[mergeNoMatches['player'] == names[playerRef]]['club'].values)
                playersScores = {tuple[0]:tuple[1] for tuple in listOfTuples}
                playersRefsClubs = {key:np.unique(self.players[self.players['Name'] == key]['Club'].values) for key in playersScores}
                playersScores = self._add_club_info_to_score(playersScores, playersRefsClubs, clubsPlayerMerge)
                

                playersPairsChosen[names[playerRef]] = max(playersScores, key=playersScores.get)
            for key, value in playersPairsChosen.items():
                fuzzyResult.loc[len(fuzzyResult)] = [key, value, fifa]

        mergeNoMatches = mergeNoMatches.dropna(axis=1).merge(fuzzyResult, left_on=['player', 'fifaGame'], right_on=['player','FIFA'], how='left').merge(self.players, on=['Name','FIFA'],how='left')
                
        result = pd.concat([perfectMatches, mergeNoMatches], axis=0).reset_index(drop=True).drop_duplicates().reset_index(drop=True)

        return result

    def _prepare_players_from_matches(self):

        players = []
        clubs = []
        fifaGames = []

        for row in range(0, len(self.matches)):
            players.extend(self.matches.iloc[row, 0:22])
            clubs.extend([self.matches.loc[row,'homeTeam'] for i in range(0,11)])
            clubs.extend([self.matches.loc[row,'awayTeam'] for i in range(0,11)])
            fifaGames.extend([self._get_fifa_game(self.matches.loc[row,'date']) for i in range(0,22)])

        result = pd.DataFrame({'player':players, 'club':clubs, 'fifaGame':fifaGames}).drop_duplicates().reset_index(drop=True)

        return result
    
    def _get_fifa_game(self, matchday):

        releaseDates = {'FIFA16':date(2015,9,22), 'FIFA17':date(2016,9,27), 'FIFA18':date(2017,9,29), 'FIFA19':date(2018,9,28),
        'FIFA20':date(2019,9,27), 'FIFA21':date(2020,10,9), 'FIFA22':date(2021,10,1), 'FIFA23':date(2022,9,30)}

        for game in range(23, 16, -1):
            if matchday >= releaseDates[f"FIFA{game}"]:
                break
        return game

    def _add_club_info_to_score(self, playersScores, playersRefsClubs, clubsPlayerMerge):
        for key in playersRefsClubs:
            if all(club in clubsPlayerMerge for club in playersRefsClubs[key]):
                playersScores[key] = playersScores[key] + 50
            elif any(club in clubsPlayerMerge for club in playersRefsClubs[key]):
                playersScores[key] = playersScores[key] + 25
        return playersScores

    