
import pandas as pd
import plotly.express as px
import os
from dash import Dash, dcc, html, Input, Output, dash_table
import openpyxl
import requests
from io import BytesIO


# Preparing your data for usage *******************************************

df = pd.read_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/Pitcher_Season_Stats.xlsx", usecols=["Name", "W", "L", "ERA", "IP", "SO", "WHIP", "GS"])

df['K/IP'] = df["SO"]/df["IP"]
df['K/IP'] = df['K/IP'].round(2)
df['WHIP'] = df['WHIP'].round(2)

#Used for filling the dropdown menu
dfPitchers = pd.read_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/Pitcher_Headshots.xlsx")

df = df.merge(dfPitchers, on="Name", how="left")

df = df[["Name", "Handedness", "GS", "W", "L", "ERA", "IP", "SO", "K/IP", "WHIP"]]

#Used for getting the game by game logs - maybe limit to last five starts?
dfGameLogs = pd.read_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/2024_Pitching_Logs.xlsx", usecols=["Name", "Date", "Opp", "W", "L", "IP", "BF", "H", "R", "ER", "HR", "BB", "SO","Pit"])
dfGameLogs['Date'] = pd.to_datetime(dfGameLogs['Date'], format="%Y-%m-%d").dt.date
dfGameLogs = dfGameLogs.rename(columns={"Opp":"Opponent"})

dfGameLogs = dfGameLogs.sort_values(by="Date", ascending=False)

#Bringing in stat splits for pitcher
dfS = pd.read_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/Season_Aggregated_Pitcher_Statistics.xlsx")

#dfS = dfS.reindex(["TBF", "Weighted AVG", "Weighted wOBA"])


dfSplits = pd.melt(dfS, id_vars=["Pitcher", "Team", "Handedness", "Opposing Team", "Name", "Rotowire Name", "Split", "Baseball Savant Name"], var_name="Statistic", value_name="Value")

#Testing for now
#dfSplits['Value'] = dfSplits['Value'].round(3)

#Used for showing the percentile graph
dfpct = pd.read_csv("https://github.com/mtdewrocks/matchup/raw/main/assets/Pitcher_Percentile_Rankings.csv")
dfpct = dfpct.rename(columns={"fb_velocity":"Fastball Velo", "exit_velocity":"Avg Exit Velocity", "k_percent":"K %", "chase_percent":"Chase %",
                              "whiff_percent":"Whiff %", "brl_percent":"Barrel %", "hard_hit_percent":"Hard-Hit %", "bb_percent":"BB %"})
dfpct = pd.melt(dfpct, id_vars=["player_name", "player_id", "year"], var_name="Statistic", value_name="Percentile")

#Used for the hitter table
dfHitters = pd.read_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/Combined_Daily_Data.xlsx", usecols=["fg_name", "Bats", "Batting Order", "Average", "wOBA",
                                   "ISO", "K%", "BB%", "BB%", "Fly Ball %", "Hard Contact %", "Pitcher", 
                                   "Pitcher Average", "Pitcher K%"])


               
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

stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = Dash(__name__, external_stylesheets=stylesheets)
server = app.server

image = ""

app.layout = html.Div(
    [html.Div(html.H1("MLB Matchup Analysis", id="title", style={"textAlign":"center"}), className="row"),
    html.Div([html.Div(dcc.Dropdown(
            id="pitcher-dropdown", multi=False, options=[{"label": x, "value":x} for x in sorted(dfPitchers["Name"])]
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
     html.Div(html.Div(dash_table.DataTable(id="hitter-table", data=dfHitters.to_dict("records"), style_cell={"textAlign":"center"}, style_data_conditional=hitter_style),style={"padding-top":"25px"}, className="row"))])


@app.callback(
    [Output(component_id="pitcher-picture", component_property="style"), Output(component_id="pcts-graph", component_property="style")],
    [Input(component_id="pitcher-dropdown", component_property="value")], prevent_initial_call=True)

def show_visibility(chosen_value):
    try:
        if len(chosen_value)>0:
            return {"display":"block"}, {"display":"block"}
        if len(chosen_value)==0:
            return {"display":"none"}, {"display":"none"}
    except:
        return {"display":"none"}, {"display":"none"}

@app.callback(
    Output(component_id="pitcher-picture", component_property="src"),
    [Input(component_id="pitcher-dropdown", component_property="value")], prevent_initial_call=True)

def update_picture(chosen_value):
    print(f"Values chosen by user: {chosen_value}")
    beginning_path = "https://github.com/mtdewrocks/matchup/raw/main/assets/"
    adjusted_name = chosen_value.split()
    if len(adjusted_name)==2:
        adjusted_chosen_value = adjusted_name[0] + "%20" + adjusted_name[1] + ".jpg"
        image = beginning_path + adjusted_chosen_value
    elif len(adjusted_name)==3:
        adjusted_chosen_value = adjusted_name[0] + "%20" + adjusted_name[1] + "%20" + adjusted_name[2] + ".jpg"
        image = beginning_path + adjusted_chosen_value
    print(image)
    if chosen_value!=None:
        return image


@app.callback(
    [Output(component_id="data-table", component_property="data"), Output(component_id="hitter-table", component_property="data")],
    Input(component_id="pitcher-dropdown", component_property="value"))

def update_stats(chosen_value):
    dff = df.copy()
    dff = dff[dff.Name==chosen_value]

    dfh = dfHitters.copy()
    dfh = dfh[dfh.Pitcher==chosen_value]
    print(dfh.head())
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
    dffSplits = dffSplits[dfSplits['Name']==chosen_value]
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
    dfpcts = dfpcts[dfpcts['player_name']==chosen_value]
    fig = px.bar(dfpcts, x="Percentile", y="Statistic", title="2024 MLB Percentile Rankings", category_orders={"Statistic": ['xera', 'xba', 'Fastball Velo', 'Avg Exit Velocity', "Chase %", "Whiff %", "K %", "BB %", "Barrel %", "Hard-Hit %"]}, color="Percentile", orientation="h",
             color_continuous_scale="RdBu_r",
                    color_continuous_midpoint=40, text="Percentile", width=600, height=600)
    fig.update_xaxes(range=[0, 100])
    fig.update_layout(title={"x":0.5})
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
