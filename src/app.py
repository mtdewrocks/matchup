
import pandas as pd
import plotly.express as px
import os
from dash import Dash, dcc, html, Input, Output, dash_table
import openpyxl

# Preparing your data for usage *******************************************
print(os.getcwd())
df = pd.read_excel(r"https://github.com/mtdewrocks/pitchermatchupdashboard/tree/main/assets/Pitcher_Season_Stats.xlsx", usecols=["Name", "W", "L", "ERA", "IP", "SO", "WHIP", "GS"], engine="openpyxl")
dfGameLogs = pd.read_excel(r"./assets/2024 Pitching Logs.xlsx", usecols=["Name", "Date", "Opp", "W", "L", "IP", "BF", "H", "R", "ER", "HR", "BB", "SO","Pit"])
df = pd.read_excel(r"https://github.com/mtdewrocks/pitchermatchupdashboard/tree/main/assets/Pitcher_Season_Stats.xlsx", usecols=["Name", "W", "L", "ERA", "IP", "SO", "WHIP", "GS"])
df['K/IP'] = df["SO"]/df["IP"]
df['K/IP'] = df['K/IP'].round(2)
df['WHIP'] = df['WHIP'].round(2)
print(df.head())
dfGameLogs = pd.read_excel(r"./assets/2024 Pitching Logs.xlsx", usecols=["Name", "Date", "Opp", "W", "L", "IP", "BF", "H", "R", "ER", "HR", "BB", "SO","Pit"])
dfGameLogs['Date'] = pd.to_datetime(dfGameLogs['Date'], format="%Y-%m-%d").dt.date

#dfGameLogs['Date'] = "2024 " + dfGameLogs["Date"]
#dfGameLogs["Date"] = pd.to_datetime(dfGameLogs['Date'], format="%Y %B %d")
#dfGameLogs['Date'] = dfGameLogs['Date'].dt.date
#dfGameLogs["Date"] = pd.DatetimeIndex(dfGameLogs["Date"]).strftime("%Y-%m-%d")

dfGameLogs = dfGameLogs.sort_values(by="Date", ascending=False)

#Bringing in stat splits for pitcher
dfS = pd.read_excel(r"C:\Users\shawn\Python\dash\dashenv\my-first-app\assets\Season Aggregated Pitcher Statistics.xlsx")
#dfS = dfS.reindex(["TBF", "Weighted AVG", "Weighted wOBA"])

dfSplits = pd.melt(dfS, id_vars=["Pitcher", "Team", "Handedness", "Opposing Team", "Name", "Rotowire Name", "Split", "Baseball Savant Name"], var_name="Statistic", value_name="Value")

dfPitchers = pd.read_excel(r"C:\Users\shawn\Python\dash\dashenv\my-first-app\assets\Pitcher Headshots.xlsx")

dfpct = pd.read_csv(r'C:\Users\shawn\Python\dash\dashenv\my-first-app\assets\Pitcher Percentile Rankings.csv')
dfpct = pd.melt(dfpct, id_vars=["player_name", "player_id", "year"], var_name="Statistic", value_name="Percentile")

dfHitters = pd.read_excel(r"C:\Users\shawn\Python\dash\dashenv\my-first-app\assets\Combined Daily Data.xlsx", usecols=["fg_name", "Bats", "Batting Order", "Weighted AVG Hitter", "Weighted wOBA Hitter",
                                   "Weighted ISO", "Weighted K% Hitter", "Weighted BB% Hitter", 
                                   "Weighted GB% Hitter", "Weighted FB% Hitter", "Weighted Hard% Hitter", "Pitcher", 
                                   "Weighted AVG Pitcher", "Weighted K% Pitcher"])

dfHitters = dfHitters.rename(columns={"Weighted AVG Hitter":"Average", "Weighted wOBA Hitter":"wOBA", "Weighted ISO":"ISO", "Weighted K% Hitter":"K%", "Weighted BB% Hitter":"BB%",
                                      "Weighted GB% Hitter":"GB%", "Weighted FB% Hitter":"Fly Ball %", "Weighted Hard% Hitter": "Hard Contact %", "Weighted AVG Pitcher": "Pitcher Average",
                                      "Weighted K% Pitcher":"Pitcher K%"})

dfHitters['Average'] = dfHitters["Average"].round(3)
dfHitters['wOBA'] = dfHitters["wOBA"].round(3)
dfHitters['ISO'] = dfHitters["Average"].round(3)
dfHitters['K%'] = dfHitters["K%"].round(1)
dfHitters['BB%'] = dfHitters["BB%"].round(1)
dfHitters['GB%'] = dfHitters["GB%"].round(1)
dfHitters['Fly Ball %'] = dfHitters["Fly Ball %"].round(1)
dfHitters['Hard Contact %'] = dfHitters["Hard Contact %"].round(1)
dfHitters['Pitcher Average'] = dfHitters["Pitcher Average"].round(3)
dfHitters['Pitcher K%'] = dfHitters["Pitcher K%"]*100
dfHitters['Pitcher K%'] = dfHitters["Pitcher K%"].round(1)
               
#game_log_style = [{'if':{'filter_query': '{ER} > 1', 'column_id':'ER'}, 'backgroundColor':'pink'},{'if':{'filter_query': '{ER} < 1', 'column_id':'ER'}, 'backgroundColor':'blue'}]
hitter_style = [{'if':{'filter_query': '{Average} < .250', 'column_id':'Average'}, 'backgroundColor':'lightcoral'}, {'if':{'filter_query': '{Average} < 0.200', 'column_id':'Average'}, 'backgroundColor':'darkred'},\
                {'if':{'filter_query': '{Average} > 0.250', 'column_id':'Average'}, 'backgroundColor':'deepskyblue'}, {'if':{'filter_query': '{Average} > 0.275', 'column_id':'Average'}, 'backgroundColor':'lawngreen'},
                {'if':{'filter_query': '{Average} > 0.300', 'column_id':'Average'}, 'backgroundColor':'darkgreen'}, {'if':{'column_id': 'Average'},'color': 'white'}]    

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
    html.Div(dash_table.DataTable(id="game-log-table", data=dfGameLogs.to_dict("records"), style_cell={"textAlign":"center"}),
             style={"padding-top":"25px"},
             className="row"),
     html.Div([html.Div(dash_table.DataTable(id="splits-table", data=dfSplits.to_dict("records"), style_cell={"textAlign":"center"}),style={"padding-top":"25px"}, className="six columns"),
      html.Div(dcc.Graph(figure={}, id="pcts-graph", style={'display': 'none'}), className="two columns")], className="row"),
     html.Div(html.Div(dash_table.DataTable(id="hitter-table", data=dfHitters.to_dict("records"), style_cell={"textAlign":"center"}, style_data_conditional=hitter_style),style={"padding-top":"25px"}, className="row"))])


@app.callback(
    [Output(component_id="pitcher-picture", component_property="style"), Output(component_id="pcts-graph", component_property="style")],
    [Input(component_id="pitcher-dropdown", component_property="value")])

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
    [Input(component_id="pitcher-dropdown", component_property="value")])

def update_picture(chosen_value):
    print(f"Values chosen by user: {chosen_value}")
    path = "\\assets\\"
    image = path + str(chosen_value) + ".jpg"
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
    #dfFinal = dfFinal.reindex([3,0,2])
    #dfFinal = dfFinal.drop('index',axis=1)
        return dfFinal.to_dict('records')
    except:
        return dffSplits.to_dict('records')

@app.callback(
    Output(component_id="pcts-graph", component_property="figure"),
    Input(component_id="pitcher-dropdown", component_property="value"))

def show_percentiles(chosen_value):
    dfpcts = dfpct.copy()
    dfpcts = dfpcts[dfpcts['player_name']==chosen_value]
    fig = px.bar(dfpcts, x="Percentile", y="Statistic", category_orders={"Statistic": ['brl', 'k_percent', 'chase_percent', 'whiff_percent']}, color="Percentile", orientation="h",
             color_continuous_scale="RdBu_r",
                    color_continuous_midpoint=40, text="Percentile", width=600, height=600)
    fig.update_xaxes(range=[0, 100])
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
