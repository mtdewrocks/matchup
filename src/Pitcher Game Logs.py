import os
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
import lxml
import datetime
from datetime import date, timedelta, datetime
import numpy as np
from selenium.webdriver.chrome.service import Service

os.chdir(r"C:\Users\shawn\Python\Baseball\Season Statistics")


beginningTime = time.time()

url = 'https://www.baseball-reference.com/leagues/daily.fcgi?request=1&type=p&dates=yesterday&level=mlb&franch=ANY'
#url = 'https://www.baseball-reference.com/leagues/daily.fcgi?request=1&type=p&dates=lastndays&lastndays=2&since=2024-06-01&fromandto=2024-06-01.2024-06-30&level=mlb&franch=ANY'
service = Service(executable_path=r'C:\Users\shawn\Python\Baseball\chromedriver.exe')
browser = webdriver.Chrome(service=service)
browser.maximize_window()
browser.get(url)

dfStats = []
table =  WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.ID, 'div_daily')))
soup = BeautifulSoup(table.get_attribute('outerHTML'), 'html5lib')
dfData = pd.read_html(str(soup))[0]
browser.close()
dfData = dfData[dfData['Name']!='Name']


today = (time.strftime("%Y-%m-%d"))
date_yesterday = datetime.strptime(today, "%Y-%m-%d")-timedelta(days=1)

yesterday = date_yesterday.date()
#yesterday = date_yesterday.strftime("%B"+ " " + "%d")
dfData['Date'] = yesterday


#dfLog = pd.read_excel("2024 Pitching Logs.xlsx")
#dfFinal = pd.concat([dfLog, dfData])
#dfFinal = dfFinal.drop_duplicates(subset=["Name", "Date"], keep="first")
#dfFinal.to_excel("2024 Pitching Logs.xlsx", index=False)
dfData.to_excel(r"C:\Users\shawn\Python\dash\dashenv\github\matchup\assets\2025_Pitching_Logs.xlsx", index=False)

#dfPitcher = pd.read_excel(r"C:\Users\shawn\Python\Baseball\Daily Statistics\Pitcher Matchup Data.xlsx")
#dfNew = dfPitcher.merge(dfFinal, on="Name", how="inner")
#dfOld = pd.read_excel("2024 Pitcher Matchups and Game Logs.xlsx")
#dfCombined = pd.concat([dfOld, dfNew])
#dfCombined.to_excel("2024 Pitcher Matchups and Game Logs.xlsx", index=False)
