import pandas as pd
import plotly.express as px
import os
from dash import Dash, dcc, html, Input, Output, dash_table
import openpyxl
import requests
from io import BytesIO
import dash_bootstrap_components as dbc
import numpy as np

# Preparing your data for usage *******************************************

df = pd.read_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/Pitcher_Season_Stats.xlsx", usecols=["Name", "W", "L", "ERA", "IP", "SO", "WHIP", "GS"])

df['K/IP'] = df["SO"]/df["IP"]
df['K/IP'] = df['K/IP'].round(2)
df['WHIP'] = df['WHIP'].round(2)

#Used for filling the dropdown menu
dfPitchers = pd.read_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/Pitcher_Headshots.xlsx")

df = df.merge(dfPitchers, left_on="Name", right_on="Baseball_Savant_Name", how="left")

df = df.rename(columns={"Name_y":"Name"}).drop("Name_x", axis=1)
df = df[["Name", "Baseball_Savant_Name", "Handedness", "GS", "W", "L", "ERA", "IP", "SO", "K/IP", "WHIP"]]

#Used for getting the game by game logs - maybe limit to last five starts?
dfGameLogs = pd.read_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/2024_Pitching_Logs.xlsx", usecols=["Name", "Date", "Opp", "W", "L", "IP", "BF", "H", "R", "ER", "HR", "BB", "SO","Pit"])
dfGameLogs['Date'] = pd.to_datetime(dfGameLogs['Date'], format="%Y-%m-%d").dt.date
dfGameLogs = dfGameLogs.rename(columns={"Opp":"Opponent"})

##dfGameLogs = dfGameLogs.merge(dfPitchers, left_on="Name", right_on="Baseball_Savant_Name", how="inner")
##dfGameLogs = dfGameLogs.drop(['URL', 'Handedness'], axis=1)


dfGameLogs = dfGameLogs.sort_values(by="Date", ascending=False)
##dfGameLogs = dfGameLogs.rename(columns={"Name_y":"Name"}).drop("Name_x", axis=1)

#Bringing in stat splits for pitcher
dfS = pd.read_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/Season_Aggregated_Pitcher_Statistics.xlsx")

#dfS = dfS.reindex(["TBF", "Weighted AVG", "Weighted wOBA"])


dfSplits = pd.melt(dfS, id_vars=["Pitcher", "Team", "Handedness", "Opposing Team", "Name", "Rotowire Name", "Split", "Baseball Savant Name"], var_name="Statistic", value_name="Value")

#Testing for now
#dfSplits['Value'] = dfSplits['Value'].round(3)

#Used for showing the percentile graph
dfpct = pd.read_csv("https://github.com/mtdewrocks/matchup/raw/main/assets/Pitcher_Percentile_Rankings.csv")
dfpct = dfpct.rename(columns={"xera":"Expected ERA", "xba":"Expected Batting Avg", "fb_velocity":"Fastball Velo", "exit_velocity":"Avg Exit Velocity", "k_percent":"K %", "chase_percent":"Chase %",
                              "whiff_percent":"Whiff %", "brl_percent":"Barrel %", "hard_hit_percent":"Hard-Hit %", "bb_percent":"BB %"})

dfpct = dfpct[['player_name', 'player_id', 'year', 'Expected ERA', 'Expected Batting Avg', 'Fastball Velo', 'Avg Exit Velocity', 'Chase %', 'Whiff %', 'K %', 'BB %', 'Barrel %', 'Hard-Hit %']]
dfpct = pd.melt(dfpct, id_vars=["player_name", "player_id", "year"], var_name="Statistic", value_name="Percentile")
##dfpct = dfpct.merge(dfPitchers, left_on="player_name", right_on="Baseball_Savant_Name", how="inner")
##dfpct = dfpct.drop(['URL', 'Handedness'], axis=1)

#Gets Hitters with Over .350 avg and 20 AB in last week
dfLast7 = pd.read_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/Last_Week_Stats.xlsx")

dfHot = dfLast7.query("PA>=20 & BA>=.350")

dfLastWeek = dfLast7[['Name', 'BA']]
dfLastWeek = dfLastWeek.rename(columns={"BA":"Last Week Average"} )

#Used for the hitter table
dfHitters = pd.read_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/Combined_Daily_Data.xlsx")


dfHittersFinal = dfHitters.merge(dfLastWeek, left_on="Savant Name", right_on="Name", how="left")
dfHittersFinal = dfHittersFinal.drop(["Name", "fg_name"],  axis=1)

dfProps = pd.read_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/Daily_Props.xlsx", usecols=["Player", "Over Price", "Line", "market", "bookmakers", "Under Price"])
dfProps["Line"] = dfProps["Line"].astype(float)

dfHitProps = dfProps.query("market == 'hits' and bookmakers=='draftkings'")
dfHitProps = dfHitProps.rename(columns={"Over Price":"Hits Over", "Line":"Hits Line", "Under Price":"Hits Under"})
dfHitProps = dfHitProps.drop(["market", "bookmakers"], axis=1)

dfKProps = dfProps.query("market == 'strikeouts' and bookmakers=='draftkings'")
dfKProps = dfKProps.rename(columns={"Over Price":"Strikeouts Over", "Line":"Strikeouts Line", "Under Price":"Strikeouts Under"})
dfKProps = dfKProps.drop(["market", "bookmakers"], axis=1)

dfCombinedProps = dfHitProps.merge(dfKProps, on="Player", how="inner")


dfHittersProps = dfHittersFinal.merge(dfCombinedProps, left_on="Props Name", right_on="Player", how="left")
dfHittersProps = dfHittersProps.drop("Props Name", axis=1)
                                                                                                                     #"Pitcher", 

dfHittersProps['Exclude_K'] = np.where((dfHittersProps["High K Hitter"] == 1) & (dfHittersProps["Pitcher K%"]>.20),1,0)
dfHittersProps['Exclude_Order'] = np.where(dfHittersProps["Batting Order"] >=7,1,0)
dfHittersProps['Exclude_BB'] = np.where((dfHittersProps["BB%"] > 12) & (dfHittersProps["Weighted BB% Pitcher"]>.10),1,0)
dfHittersProps['Exclude_Avg'] = np.where((dfHittersProps["Average"] < .250) | (dfHittersProps["Pitcher Average"]<.250),1,0)

dfHittersProps['Exclude'] = np.sum(dfHittersProps[['Exclude_K', 'Exclude_Order', 'Exclude_BB', 'Exclude_Avg']],axis=1)

print('printing hitters props shape')
print(dfHittersProps.shape)


dfTopMatchups = dfHittersProps.copy()
dfTopMatchups = dfTopMatchups.query("Exclude==0")
dfTopMatchups = dfTopMatchups[dfTopMatchups["Hits Line"]<1]
print(dfTopMatchups.shape)


dfHighK = dfHittersProps.copy()
dfHighK = dfHighK[(dfHighK["High K Hitter"]==1) & (dfHighK["Pitcher K%"]>=.23)]
#dfHighK = dfHighK.query("('High K Hitter'== 1) and ('Pitcher K%'>=.23")
dfHighK = dfHighK[dfHighK["Strikeouts Line"]<1]

dfLowK = dfHittersProps.copy()

dfLowK = dfLowK[(dfLowK["K%"]<=15) & (dfLowK["Pitcher K%"]<=18)]
#dfLowK = dfLowK.query("'Weighted K% Hitter'<=15 & 'Weighted K% Pitcher'<=.15")

#game_log_style = [{'if':{'filter_query': '{ER} > 1', 'column_id':'ER'}, 'backgroundColor':'pink'},{'if':{'filter_query': '{ER} < 1', 'column_id':'ER'}, 'backgroundColor':'blue'}]
hitter_style = [{'if':{'filter_query': '{Average} < .250', 'column_id':'Average'}, 'backgroundColor':'lightcoral'}, {'if':{'filter_query': '{Average} < 0.200', 'column_id':'Average'}, 'backgroundColor':'darkred'},\
                {'if':{'filter_query': '{Average} >= 0.250', 'column_id':'Average'}, 'backgroundColor':'dodgerblue'}, {'if':{'filter_query': '{Average} >= 0.275', 'column_id':'Average'}, 'backgroundColor':'blue'},
                {'if':{'filter_query': '{Average} > 0.300', 'column_id':'Average'}, 'backgroundColor':'darkgreen'}, {'if':{'column_id': 'Average'},'color': 'white'},\
                {'if':{'filter_query': '{wOBA} < .325', 'column_id':'wOBA'}, 'backgroundColor':'lightcoral'},{'if':{'filter_query': '{wOBA} <= 0.275', 'column_id':'wOBA'}, 'backgroundColor':'darkred'},\
                {'if':{'filter_query': '{wOBA} >= 0.325', 'column_id':'wOBA'}, 'backgroundColor':'dodgerblue'}, {'if':{'filter_query': '{wOBA} >= 0.360', 'column_id':'wOBA'}, 'backgroundColor':'blue'},
                {'if':{'filter_query': '{wOBA} > 0.400', 'column_id':'wOBA'}, 'backgroundColor':'darkgreen'}, {'if':{'column_id': 'wOBA'},'color': 'white'},
                {'if':{'filter_query': '{ISO} < .175', 'column_id':'ISO'}, 'backgroundColor':'lightcoral'},{'if':{'filter_query': '{ISO} <= 0.125', 'column_id':'ISO'}, 'backgroundColor':'darkred'},\
                {'if':{'filter_query': '{ISO} >= 0.175', 'column_id':'ISO'}, 'backgroundColor':'dodgerblue'}, {'if':{'filter_query': '{ISO} >= 0.225', 'column_id':'ISO'}, 'backgroundColor':'blue'},
                {'if':{'filter_query': '{ISO} > 0.275', 'column_id':'ISO'}, 'backgroundColor':'darkgreen'}, {'if':{'column_id': 'ISO'},'color': 'white'},
                {'if':{'filter_query': '{K%} < 25', 'column_id':'K%'}, 'backgroundColor':'lightcoral'},{'if':{'filter_query': '{K%} >= 25', 'column_id':'K%'}, 'backgroundColor':'darkred'},\
                {'if':{'filter_query': '{K%} < 20', 'column_id':'K%'}, 'backgroundColor':'dodgerblue'}, {'if':{'filter_query': '{K%} < 15', 'column_id':'K%'}, 'backgroundColor':'blue'},
                {'if':{'filter_query': '{K%} < 10', 'column_id':'K%'}, 'backgroundColor':'darkgreen'}, {'if':{'column_id': 'K%'},'color': 'white'}]    

stylesheets = [dbc.themes.BOOTSTRAP, "https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = Dash(__name__, external_stylesheets=stylesheets)
server = app.server

image = ""

matchup_tab = html.Div(
    [html.Div(html.H1("MLB Matchup Analysis", id="title", style={"textAlign":"center"}), className="row"),
    html.Div([html.Div(dcc.Dropdown(
            id="pitcher-dropdown", multi=False, options=[{"label": x, "value":x} for x in sorted(dfPitchers["Baseball_Savant_Name"])]
            ),
        className="two columns"),
    html.Div(
        html.Img(
            id="pitcher-picture", src=app.get_asset_url(image),alt="image", height=75, width=75, style={'display':'none', 'padding':'25px', 'padding-left':"-20px"}),
        className="one columns"),
    html.Div(
        dash_table.DataTable(
            id="data-table", data=df.to_dict("records"), style_cell={"textAlign":"center"}),
        className="six columns"),
    ], className="row"),
    html.Div(dash_table.DataTable(id="game-log-table", data=dfGameLogs.to_dict("records"), style_cell={"textAlign":"center", "fontWeight":"bold", "fontSize":"30px"}),
             style={"padding-top":"25px"},
             className="row"),
     html.Div([html.Div(dash_table.DataTable(id="splits-table", data=dfSplits.to_dict("records"), style_cell={"textAlign":"center"}),style={"padding-top":"25px"}, className="six columns"),
      html.Div(dcc.Graph(figure={}, id="pcts-graph", style={'display': 'none'}), className="two columns")], className="row"),
     html.Div(html.P(children="Splits data are from 2024.", id="splits-note", style={'display':'none', 'font-weight':'bold'}),className="row"),
     html.Div(html.Div(dash_table.DataTable(id="hitter-table", data=dfHittersFinal.to_dict("records"), style_cell={"textAlign":"center"}, style_data_conditional=hitter_style),style={"padding-top":"25px"}, className="row"))])

#image_path = 'assets/fire.jpg'
#html.Img(src=image_path)



hot_hitter_tab = dbc.Container([dbc.Row([html.H1("Hot Hitters", style={'color': 'red', 'fontSize': 40, 'textAlign':'center'})]), dbc.Row(html.H6("Statistics over the last week", style={'fontSize': 20, 'textAlign':'center'})),
                                    dbc.Row(dash_table.DataTable(id="hot-hitters", data=dfHot.to_dict("records"), style_cell={"textAlign":"center"}, sort_action="native"))])



top_hitter_matchups = dbc.Container([dbc.Row([html.H1("Top Hitter Matchups", style={'color': 'blue', 'fontSize': 40, 'textAlign':'center'})]),
                                    dbc.Row(dash_table.DataTable(id="top-matchups", data=dfTopMatchups.to_dict("records"), style_cell={"textAlign":"center"}, sort_action="native"))])


top_strikeout_matchups = dbc.Container([dbc.Row([html.H1("Top Strikeout Targets", style={'color': 'blue', 'fontSize': 40, 'textAlign':'center'})]),
                                    dbc.Row(dash_table.DataTable(id="top-strikeouts", data=dfHot.to_dict("records"), style_cell={"textAlign":"center"}, sort_action="native"))])

tabs = dbc.Tabs([dbc.Tab(matchup_tab, label="Matchup"), dbc.Tab(hot_hitter_tab, label="Hot Hitters"), dbc.Tab(top_hitter_matchups, label="Top Hitter Matchups")])
app.layout = dbc.Row(dbc.Col(tabs))


@app.callback(
    [Output(component_id="pitcher-picture", component_property="style"), Output(component_id="pcts-graph", component_property="style"), Output(component_id="splits-note", component_property="style"),],
    [Input(component_id="pitcher-dropdown", component_property="value")], prevent_initial_call=True)

def show_visibility(chosen_value):
    try:
        if len(chosen_value)>0:
            return {"display":"block"}, {"display":"block"}, {"display":'block', 'font-weight':'bold'}
        if len(chosen_value)==0:
            return {"display":"none"}, {"display":"none"}, {"display":"none"}
    except:
        return {"display":"none"}, {"display":"none"}, {"display":"none"}

@app.callback(
    Output(component_id="pitcher-picture", component_property="src"),
    [Input(component_id="pitcher-dropdown", component_property="value")], prevent_initial_call=True)

def update_picture(chosen_value):
    beginning_path = "https://github.com/mtdewrocks/matchup/raw/main/assets/"
    dfpicture = dfPitchers.copy()
    dfpicture = dfpicture[dfpicture["Baseball_Savant_Name"]==chosen_value]
    name = dfpicture["Name"].values[0]
    adjusted_name = name.split()
    print('print name')
    print(name)
    if len(adjusted_name)==2:
        adjusted_chosen_value = adjusted_name[0] + "%20" + adjusted_name[1] + ".jpg"
        image = beginning_path + adjusted_chosen_value
    elif len(adjusted_name)==3:
        adjusted_chosen_value = adjusted_name[0] + "%20" + adjusted_name[1] + "%20" + adjusted_name[2] + ".jpg"
        image = beginning_path + adjusted_chosen_value
    
    if chosen_value!=None:
        return image


@app.callback(
    [Output(component_id="data-table", component_property="data"), Output(component_id="hitter-table", component_property="data")],
    Input(component_id="pitcher-dropdown", component_property="value"))

def update_stats(chosen_value):
    dff = df.copy()
    dff = dff[dff["Baseball_Savant_Name"]==chosen_value]
    dfh = dfHittersProps.copy()
    dfh = dfh[["fg_name", "Savant Name", "Props Name", "Bats", "Batting Order", "Average", "wOBA",
                                   "ISO", "K%", "BB%", "Baseball Savant Name"]]
    dfh = dfh[dfh["Baseball Savant Name"]==chosen_value]
    dfh = dfh.sort_values(by="Batting Order")
    dfh = dfh.drop(["Baseball Savant Name"], axis=1)
    return dff.to_dict('records'), dfh.to_dict('records')

@app.callback(
    Output(component_id="game-log-table", component_property="data"),
    Input(component_id="pitcher-dropdown", component_property="value"))

def update_game_logs(chosen_value):
    dffgame = dfGameLogs.copy()
    dffgame = dffgame[dffgame.Name==chosen_value]
    print('printing game logs')
    print(dffgame.head())
    dffgame = dffgame.drop("Name", axis=1)
    return dffgame.to_dict('records')

@app.callback(
    Output(component_id="splits-table", component_property="data"),
    Input(component_id="pitcher-dropdown", component_property="value"))

def show_pitcher_splits(chosen_value):
    dffSplits = dfSplits.copy()
    dffSplits = dffSplits[dfSplits['Baseball Savant Name']==chosen_value]
    try:
        dfPivot = dffSplits.pivot_table('Value', index='Statistic', columns='Split')
        dfPivot = dfPivot.reset_index()
        cols = ["vs L", "Statistic", "vs R"]
        dfFinal = dfPivot[cols]
        dfFinal = dfFinal.reset_index()
        dfFinal = dfFinal.reindex([3,4,5,17,15,1,0,2,12,6,9,13,7,10,16,14,11,8,18])
        dfFinal = dfFinal.drop('index',axis=1)
        return dfFinal.to_dict('records')
    except:
        return dffSplits.to_dict('records')

@app.callback(
    Output(component_id="pcts-graph", component_property="figure"),
    Input(component_id="pitcher-dropdown", component_property="value"))

def show_percentiles(chosen_value):
    dfpcts = dfpct.copy()
    print(chosen_value)
    dfpcts = dfpcts[dfpcts['player_name']==chosen_value]
    print('dfpcts')
    print(dfpcts)
    fig = px.bar(dfpcts, x="Percentile", y="Statistic", title="2024 MLB Percentile Rankings", category_orders={"Statistic": ['Fastball Velo', 'Avg Exit Velocity', "Chase %", "Whiff %", "K %", "BB %", "Barrel %", "Hard-Hit %"]}, color="Percentile", orientation="h",
             color_continuous_scale="RdBu_r",
                    color_continuous_midpoint=40, text="Percentile", width=600, height=600)
    fig.update_xaxes(range=[0, 100])
    #fig.update_layout(title_x=0.5, title_font_weight="bold", layout_coloraxis_showscale=False)
    fig.update(layout_coloraxis_showscale=False)
    return fig


#May need to restructure percentile data to accomodate sort order as follows
#category_orders={'month':['January', 'February', 'March',
                                  #      'April', 'May', 'June', 'July', 
                                   #     'August', 'September', 'October', 'November', 'December']}

#app.layout = html.Div([dcc.Dropdown(id="pitcher-dropdown", multi=False, options=[{"label": x, "value":x} for x in sorted(df["Name"])], value=["Justin Verlander"]),
#                     html.A(id="pitcher-link", children="Click here to navigate", href="https://www.espn.com", target="_blank")]), className= "two columns")




if __name__ == "__main__":
    app.run_server(debug=True)
