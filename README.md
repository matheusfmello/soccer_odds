# soccerOdds

![InProgress](https://img.shields.io/badge/Status-In%20progress-yellow)

This work's goal is to predict soccer matches results and compare them to betting odds.

The initial target is to predict only the match result based on recent team's forms and also player attributes extracted from FIFA game.

# Install

The following commands set the environment ready for anaconda users

```
conda create env --name <myEnv>
conda activate <myEnv>
pip install -r requirements.txt
```

# Further releases

The first results are not satisfactory yet. Some of the improvements ideas to be implemented in the future are listed below:

- Scrapping more matches results to enrich the training set
- Scrapping Football Manager players attributes, as they are a better source of information, especially in minor leagues

- Predicting not only the match result, but also the ammount of goals and other metrics
- Creating a trigger advising if a match odd differs from the model's predicted results (profit opportunities)
- Creating a backtest simulator to analyse different betting strategies.
