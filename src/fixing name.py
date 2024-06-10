import pandas as pd

dfPitchers = pd.read_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/Pitcher_Headshots.xlsx")

#Testing for now
#dfSplits['Value'] = dfSplits['Value'].round(3)

#Used for showing the percentile graph
dfpct = pd.read_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/Pitcher_Percentile_Rankings.xlsx")
dfpct = dfpct.rename(columns={"xera":"Expected ERA", "xba":"Expected Batting Avg", "fb_velocity":"Fastball Velo", "exit_velocity":"Avg Exit Velocity", "k_percent":"K %", "chase_percent":"Chase %",
                              "whiff_percent":"Whiff %", "brl_percent":"Barrel %", "hard_hit_percent":"Hard-Hit %", "bb_percent":"BB %"})

dfpct = dfpct[['player_name', 'player_id', 'year', 'Expected ERA', 'Expected Batting Avg', 'Fastball Velo', 'Avg Exit Velocity', 'Chase %', 'Whiff %', 'K %', 'BB %', 'Barrel %', 'Hard-Hit %']]
dfpct = pd.melt(dfpct, id_vars=["player_name", "player_id", "year"], var_name="Statistic", value_name="Percentile")
print(dfpct.shape)
dfpct = dfpct.merge(dfPitchers, left_on="player_name", right_on="Baseball_Savant_Name", how="inner")
dfpct = dfpct.drop(['URL', 'Handedness'], axis=1)
print(dfpct.head())
