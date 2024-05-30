#Pitching Stats for Season

##Baseball Reference Data

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

#os.chdir(r"C:\Users\shawn\Python\Baseball\Season Statistics")


beginningTime = time.time()

url = 'https://www.baseball-reference.com/leagues/daily.fcgi?request=1&type=p&dates=since&since=2024-03-01&level=mlb&franch=ANY'
browser = webdriver.Chrome()
browser.maximize_window()
browser.get(url)

dfStats = []
table =  WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.ID, 'div_daily')))
soup = BeautifulSoup(table.get_attribute('outerHTML'), 'html5lib')
dfData = pd.read_html(str(soup))[0]

#Dropping headers rows with Name
dfData = dfData[dfData['Name']!="Name"]
#dfData.to_excel("Pitcher Season Stats.xlsx", sheet_name="Season", index=False)
dfData.to_excel("https://github.com/mtdewrocks/matchup/raw/main/assets/Pitcher_Season_Stats.xlsx", sheet_name="Season", index=False)
browser.close()
