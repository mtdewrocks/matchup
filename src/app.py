import pandas as pd
import plotly.express as px
import os
from dash import Dash, dcc, html, Input, Output, dash_table
import openpyxl
import requests
from io import BytesIO
import dash_bootstrap_components as dbc

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


#Used for showing the percentile graph
dfpct = pd.read_csv("https://github.com/mtdewrocks/matchup/raw/main/assets/Pitcher_Percentile_Rankings.csv")
dfpct = dfpct.rename(columns={"xera":"Expected ERA", "xba":"Expected Batting Avg", "fb_velocity":"Fastball Velo", "exit_velocity":"Avg Exit Velocity", "k_percent":"K %", "chase_percent":"Chase %",
                              "whiff_percent":"Whiff %", "brl_percent":"Barrel %", "hard_hit_percent":"Hard-Hit %", "bb_percent":"BB %"})

dfpct = dfpct.drop("year", axis=1)
suffix = '_pitcher'
dfpct = dfpct.rename(columns=lambda x: x + suffix)

dfpct = dfpct[['player_name_pitcher', 'player_id_pitcher', 'Expected ERA', 'Expected Batting Avg_pitcher', 'Fastball Velo_pitcher', 'Avg Exit Velocity_pitcher', 'Chase %_pitcher', 'Whiff %_pitcher', 'K %_pitcher', 'BB %_pitcher', 'Barrel %_pitcher', 'Hard-Hit %_pitcher']]
dfpct_reshaped = pd.melt(dfpct, id_vars=["player_name", "player_id", "year"], var_name="Statistic", value_name="Percentile")

#Gets Hitters with Over .350 avg and 20 AB in last week
dfLast7 = pd.read_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/Last_Week_Stats.xlsx")

dfHot = dfLast7.query("PA>=20 & BA>=.350")

dfLastWeek = dfLast7[['Name', 'BA']]
dfLastWeek = dfLastWeek.rename(columns={"BA":"Last Week Average"} )

#Used for the hitter table
dfDaily = pd.read_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/Combined_Daily_Data.xlsx")
dfHitters = dfDaily[["fg_name", "Savant Name", "Bats", "Batting Order", "Average", "wOBA",
                                   "ISO", "K%", "BB%", "Fly Ball %", "Hard Contact %", "Pitcher", "Baseball Savant Name"]]

df_hitter_pct = pd.read_csv("https://github.com/mtdewrocks/matchup/raw/main/assets/Hitter_Percentile_Rankings.csv", usecols=['player_name', 'xwoba','xba',
                            'xslg',	'xiso',	'xobp',	'brl_percent',	'exit_velocity', 'hard_hit_percent', 'k_percent','bb_percent','whiff_percent','chase_percent'])

df_hitter_pct = df_hitter_pct.drop("year", axis=1)
suffix = '_hitter'
df_hitter_pct = df_hitter_pct.rename(columns=lambda x: x + suffix)

dfHittersFinal = dfHitters.merge(dfLastWeek, left_on="Savant Name", right_on="Name", how="left")
dfHittersFinal = dfHittersFinal.drop("Name", axis=1)

dfHitterMerge = dfDaily.merge(df_hitter_pct, left_on="Savant Name", right_on="player_name", how="left")
dfFinalMatchup = dfHitterMerge.merge(dfpct, left_on="Baseball Savant Name", right_on="player_name", how="left", suffixes=["_Hitter", "_Pitcher"])

df_props = pd.read_excel('https://github.com/mtdewrocks/matchup/raw/main/assets/Daily_Props.xlsx')
df_pitchers = pd.read_excel('https://github.com/mtdewrocks/matchup/raw/main/assets/My_Pitcher_Listing.xlsx', usecols=["Props Name", "mlb_team_long"])
df_hitters = pd.read_excel('https://github.com/mtdewrocks/matchup/raw/main/assets/My_Hitter_Listing.xlsx', usecols=["Props Name", "mlb_team_long"])

df_players = pd.concat([df_pitchers, df_hitters])
df_daily_props = df_props.merge(df_players, left_on="Player", right_on="Props Name", how="left")

df_daily_props = df_daily_props.dropna(subset=["mlb_team_long"])

df_props_matchup = df_daily_props.merge(dfFinalMatchup, on=["Props Name", "mlb_team_long"], how="left")


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




#df_daily_props.to_excel(r'C:\Users\shawn\Python\Baseball\Daily Statistics\Testing Props.xlsx', index=False)

#unique_teams = df_daily_props['mlb_team_long'].unique()


#team_options = [{"label": value, "value": value} for value in unique_teams]
props_tab = html.Div(
    [html.Div(html.H1("Player Props Analysis", id="props-title", style={"textAlign":"center"}), className="row"),
    html.Div(html.Br()),
    html.Div([html.Div(dcc.Dropdown(
            id="mlb-team-dropdown", multi=False, options=[{"label": x, "value":x} for x in sorted(df_daily_props["mlb_team_long"].unique())],
            ),
        className="three columns"),
    html.Div(dcc.Dropdown(
            id="mlb-player-dropdown", multi=False, options=[{"label": x, "value":x} for x in sorted(df_daily_props["Player"].unique())],
            ),
        className="three columns"),
    html.Div(dcc.Dropdown(
            id="market-dropdown", multi=False, options=[{"label": x, "value":x} for x in sorted(df_daily_props["market"].unique())],
            ),
        className="three columns"),
    html.Div(dcc.Dropdown(
            id="bookmaker-dropdown", multi=False, options=[{"label": x, "value":x} for x in sorted(df_daily_props["bookmakers"].unique())],
            ),
        className="three columns")], className="row"),
        html.Div(
        dash_table.DataTable(
            id="props-data-table", data=df_daily_props.to_dict("records"), style_table={'margin-top':'15px'}, style_cell={"textAlign":"center"}, sort_action="native"),
        className="six columns")])


#image_path = 'assets/fire.jpg'
#html.Img(src=image_path)

hot_hitter_tab = dbc.Container([dbc.Row([html.H1("Hot Hitters", style={'color': 'red', 'fontSize': 40, 'textAlign':'center'})]), dbc.Row(html.H6("Statistics over the last week", style={'fontSize': 20, 'textAlign':'center'})),
                                    dbc.Row(dash_table.DataTable(id="hot-hitters", data=dfHot.to_dict("records"), style_cell={"textAlign":"center"}, sort_action="native"))])

tabs = dbc.Tabs([dbc.Tab(matchup_tab, label="Matchup"), dbc.Tab(hot_hitter_tab, label="Hot Hitters"), dbc.Tab(props_tab, label="Player Props")])
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
    dfh = dfHittersFinal.copy()
    dfh = dfh[dfh["Baseball Savant Name"]==chosen_value]
    dfh = dfh.sort_values(by="Batting Order")
    dfh = dfh.drop("Pitcher", axis=1)
    return dff.to_dict('records'), dfh.to_dict('records')

@app.callback(
    Output(component_id="game-log-table", component_property="data"),
    Input(component_id="pitcher-dropdown", component_property="value"))

def update_game_logs(chosen_value):
    dffgame = dfGameLogs.copy()
    dffgame = dffgame[dffgame.Name==chosen_value]
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
    dfpcts = dfpct_reshaped.copy()
    dfpcts = dfpcts[dfpcts['player_name']==chosen_value]
    fig = px.bar(dfpcts, x="Percentile", y="Statistic", title="2024 MLB Percentile Rankings", category_orders={"Statistic": ['Fastball Velo', 'Avg Exit Velocity', "Chase %", "Whiff %", "K %", "BB %", "Barrel %", "Hard-Hit %"]}, color="Percentile", orientation="h",
             color_continuous_scale="RdBu_r",
                    color_continuous_midpoint=40, text="Percentile", width=600, height=600)
    fig.update_xaxes(range=[0, 100])
    #fig.update_layout(title_x=0.5, title_font_weight="bold", layout_coloraxis_showscale=False)
    fig.update(layout_coloraxis_showscale=False)
    return fig


#Update players available
@app.callback(
    Output("mlb-player-dropdown", "options"),
    [Input("mlb-team-dropdown", "value")], prevent_initial_call=True)
def update_players(selected_team):
    if selected_team:
        players = df_daily_props[df_daily_props["mlb_team_long"] == selected_team]["Player"].unique()
        return [{"label": player, "value": player} for player in players]
    else:
        return df_daily_props["Player"].unique()

#Update markets available

@app.callback(
    Output("market-dropdown", "options"),
    [Input("mlb-player-dropdown", "value")], prevent_initial_call=True)

def update_market(selected_market):
    if selected_market:
        markets = df_daily_props[df_daily_props["Player"] == selected_market]["market"].unique()
        return [{"label": market, "value": market} for market in markets]
    else:
        return df_daily_props["market"].unique()

@app.callback(
    Output(component_id="props-data-table", component_property="data"),
    [Input(component_id="mlb-team-dropdown", component_property="value"), Input(component_id="mlb-player-dropdown", component_property="value"),
     Input(component_id="market-dropdown", component_property="value"), Input(component_id="bookmaker-dropdown", component_property="value")])

def update_stats(chosen_team, chosen_player, chosen_market, chosen_bookmaker):
    dff_props = df_props_matchup.copy()
    dff_props = dff_props.drop(["commence_time", "Props Name", "home_team", "away_team", "fg_name", "Savant Name", "Split Hitter", "HR Hitter", "SB", "CS", "Bats",
                                "GB%", "Fly Ball %", "wOBA", "Weighted OBP", "Weighted Slugging", "Weighted OBPS", "Team", "Handedness", "Opposing Team",
                                "Baseball Savant Name", "Split Pitcher", "Weighted FIP", "Weighted GB% Pitcher", "Weighted FB% Pitcher", "Weighted HR/FB",
                                "player_name_Hitter", "player_name_Pitcher", "player_id", "year"], axis=1)
    if chosen_team:
        dff_props = dff_props[dff_props["mlb_team_long"] == chosen_team]
    if chosen_player:
        dff_props = dff_props[dff_props["Player"] == chosen_player]
    if chosen_market:
        dff_props = dff_props[dff_props["market"] == chosen_market]
        if chosen_market=="hits":
            dff_props = dff_props[["Player", "market", "bookmakers", "Line", "Over Price", "Under Price", "Batting Order", "Average", "K%", "BB%", "Pitcher Average", "Pitcher K%", "Weighted BB% Pitcher", "Expected Batting Avg_hitter", "Expected Batting Avg_pitcher"]]
        if chosen_market=="strikeouts":
            dff_props = dff_props[["Player", "market", "bookmakers", "Line", "Over Price", "Under Price", "Batting Order", "Average", "K%", "BB%", "Whiff %_hitter", "Chase %_hitter", "Pitcher K%", "Weighted BB% Pitcher", "Whiff %_pitcher", "Chase %_pitcher"]]
    if chosen_bookmaker:
        dff_props = dff_props[dff_props["bookmakers"] == chosen_bookmaker]
    #
    #dff_props = dff_props.reindex(columns=["Player", "market", "bookmakers", "Line", "Over Price", "Under Price"])
    return dff_props.to_dict('records')


#May need to restructure percentile data to accomodate sort order as follows
#category_orders={'month':['January', 'February', 'March',
                                  #      'April', 'May', 'June', 'July', 
                                   #     'August', 'September', 'October', 'November', 'December']}

#app.layout = html.Div([dcc.Dropdown(id="pitcher-dropdown", multi=False, options=[{"label": x, "value":x} for x in sorted(df["Name"])], value=["Justin Verlander"]),
#                     html.A(id="pitcher-link", children="Click here to navigate", href="https://www.espn.com", target="_blank")]), className= "two columns")




if __name__ == "__main__":
    app.run_server(debug=True)
