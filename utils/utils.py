import json
from math import nan
import os
from os import read
from altair.vegalite.v4.schema.channels import Opacity, Tooltip
import codecs
import numpy as np
import pandas as pd
import geopandas as gpd
import streamlit as st
import altair as alt
from keplergl import KeplerGl
from streamlit_keplergl import keplergl_static
from millify import millify

import time
from datetime import datetime, timedelta
import streamlit.components.v1 as components

import requests
from bs4 import BeautifulSoup
import re

import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import warnings

from functools import partial
import pyproj
from shapely.ops import transform
from shapely.geometry import Point, Polygon

from empiricaldist import Pmf, Cdf

proj_wgs84 = pyproj.Proj("+proj=longlat +datum=WGS84")

warnings.filterwarnings("ignore")

colnames = [
    "Timestamp",
    "Latitude",
    "Longitude",
    "Depth",
    "Magnitude",
    "magType",
    "nst",
    "gap",
    "dmin",
    "rms",
    "net",
    "id",
    "updated",
    "Location",
    "type",
    "horizontalError",
    "depthError",
    "magError",
    "magNst",
    "status",
    "locationSource",
    "magSource",
    "DOY",
    "Month",
    "Day",
    "Year",
    "Date",
]

mapping_dict = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}

month_list = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


@st.cache(allow_output_mutation=True, show_spinner=False)
def read_data():
    data = pd.read_csv("./assets/typhoon_data.csv")
    data["ISO_TIME"] = pd.to_datetime(data.ISO_TIME)
    data["Year"] = pd.DatetimeIndex(data["ISO_TIME"]).year
    data["Month"] = pd.DatetimeIndex(data["ISO_TIME"]).month
    data["Date"] = pd.DatetimeIndex(data["ISO_TIME"]).date
    data["Date"] = pd.to_datetime(data["ISO_TIME"])
    return data


def read_path():
    world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    path = gpd.read_file("./assets/typhoon_path_dissolve.shp")

    for i in path.index:
        for j in world.geometry.iteritems():
            if path.loc[i, "geometry"].intersects(j[1]):
                path.loc[i, "Land Fall"] = 1
                break

    return path


@st.cache(allow_output_mutation=True, show_spinner=False)
def read_points():
    points = gpd.read_file("./assets/typhoon_path_points_landed.shp")
    points = points[["SID", "NAME", "ISO_TIME", "geometry"]]
    points["ISO_TIME"] = pd.to_datetime(points.ISO_TIME)
    points["Year"] = pd.DatetimeIndex(points["ISO_TIME"]).year
    points["Month"] = pd.DatetimeIndex(points["ISO_TIME"]).month
    points["Date"] = pd.DatetimeIndex(points["ISO_TIME"]).date
    points["Date"] = pd.to_datetime(points["ISO_TIME"])
    return points


def read_config(fn):
    with open(fn) as infile:
        config = json.load(infile)
        return config


@st.cache()
def read_admin():
    admin = pd.read_csv("./assets/typhoon_per_province.csv")
    return admin


@st.cache(allow_output_mutation=True, show_spinner=False)
def read_phivolcs_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSdxYJ7zl_Pgo7k5kHOcrHLmW2T9WF5nptZTVHOTXbUIVQompINuLLshM6uco7gqo_6xLTQzMBGdffH/pub?gid=576379500&single=true&output=csv"
    df = pd.read_csv(url, encoding="latin-1")
    # df = pd.read_csv('./assets/phivolcs-eq.csv', encoding='latin-1')
    # df['Date'] = df['Date'].str.strip()
    # df['Date'] = pd.to_datetime(df['Date'], format='%d %B %Y - %I:%M %p')
    # df['Latitude'] = df['Latitude'].astype('float')
    # df['Longitude'] = df['Longitude'].astype('float')
    # df['Depth'] = df['Depth'].astype('float')
    # df['Mag'] = df['Mag'].astype('float')
    # df['DOY'] = pd.DatetimeIndex(df['Date']).dayofyear
    # df['Month'] = pd.DatetimeIndex(df['Date']).month
    # df['Day'] = pd.DatetimeIndex(df['Date']).day
    # df['Year'] = pd.DatetimeIndex(df['Date']).year
    # df.columns = ['Timestamp', 'Latitude', 'Longitude', 'Depth', 'Magnitude', 'Location', 'DOY',
    #    'Month', 'Day', 'Year']
    # df['Timestamp'] = df['Timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S')
    # df['Date'] = pd.DatetimeIndex(df['Timestamp']).date
    return df

def read_eq_config(fn):
    # read text file
    with open(fn) as infile:
        config = json.load(infile)
        return config


def extract(url):
    response = requests.get(url, verify=False)
    content = response.text
    doc = BeautifulSoup(content, "html.parser")

    datetime = doc.find_all("td", {"class": ["auto-style91", "auto-style100"]})
    latitude = doc.find_all("td", class_="auto-style90")
    longitude = doc.find_all(
        "td",
        {
            "class": "auto-style56",
            "style": "width: 92px; height: 30px; border-left-style: none; border-right: 1pt solid mistyrose; border-top: 1pt solid mistyrose; border-bottom: 1pt solid mistyrose; padding: 0.75pt; background: white",
        },
    )
    depth = doc.find_all(
        "td",
        {
            "class": "auto-style56",
            "style": "width: 62px; height: 30px; border-left-style: none; border-right: 1pt solid mistyrose; border-top: 1pt solid mistyrose; border-bottom: 1pt solid mistyrose; padding: 0.75pt; background: white",
        },
    )
    magnitude = doc.find_all(
        "td",
        {
            "class": ["auto-style56", "auto-style110"],
            "style": "width: 52px; height: 30px; border-left-style: none; border-right: 1pt solid mistyrose; border-top: 1pt solid mistyrose; border-bottom: 1pt solid mistyrose; padding: 0.75pt; background: white",
        },
    )
    location = doc.find_all("td", class_="auto-style52")

    datetime_list = []
    # bulletin_list = []
    for i in datetime:
        datetime_list.append(re.sub("[^A-Za-z0-9: ]+", "", i.text.strip()))
        # bulletin_list.append(url + i.find('a')['href'].replace('\\','/').replace('../../',''))

    latitude_list = []
    for i in latitude:
        latitude_list.append(i.text.strip().replace("-", ""))

    longitude_list = []
    for i in longitude:
        longitude_list.append(i.text.strip().replace("-", ""))

    depth_list = []
    for i in depth:
        depth_list.append(i.text.strip().replace("-", ""))

    magnitude_list = []
    for i in magnitude:
        magnitude_list.append(i.text.strip().replace("-", ""))

    location_list = []
    for i in location:
        location_list.append(re.sub("[^A-Za-z0-9 ]+", "", i.text.strip()))

    temp_dict = {
        "Date": datetime_list,
        "Latitude": latitude_list,
        "Longitude": longitude_list,
        "Depth": depth_list,
        "Mag": magnitude_list,
        "Location": location_list,
        # 'Bulletin Link': bulletin_list
    }

    df = pd.DataFrame(temp_dict)

    df["Date"] = df["Date"].str.strip()
    df["Date"] = pd.to_datetime(df["Date"], format="%d %B %Y %I:%M %p")
    df["Latitude"] = df["Latitude"].astype("float")
    df["Longitude"] = df["Longitude"].astype("float")
    df["Depth"] = df["Depth"].astype("float")
    df["Mag"] = df["Mag"].astype("float")
    df["DOY"] = pd.DatetimeIndex(df["Date"]).dayofyear
    df["Month"] = pd.DatetimeIndex(df["Date"]).month
    df["Day"] = pd.DatetimeIndex(df["Date"]).day
    df["Year"] = pd.DatetimeIndex(df["Date"]).year
    df["Hour"] = pd.DatetimeIndex(df["Date"]).hour
    df["Minute"] = pd.DatetimeIndex(df["Date"]).minute
    df["AMPM"] = pd.DatetimeIndex(df["Date"]).strftime("%p")
    df.columns = [
        "Timestamp",
        "Latitude",
        "Longitude",
        "Depth",
        "Magnitude",
        "Location",
        "DOY",
        "Month",
        "Day",
        "Year",
        "Hour",
        "Minute",
        "AMPM",
    ]
    df["Timestamp"] = df["Timestamp"].dt.strftime("%Y-%m-%dT%I:%M:%S %p")
    df["Date"] = pd.DatetimeIndex(df["Timestamp"]).date

    return df


def update_phivolcs():
    phivolcs_df = read_phivolcs_data()

    phivolcs_df["Timestamp"] = pd.to_datetime(
        phivolcs_df["Timestamp"], format="%Y-%m-%dT%I:%M:%S %p"
    )
    max_date = phivolcs_df["Date"].max()

    url = "https://earthquake.phivolcs.dost.gov.ph/"
    df = extract(url)
    df = df[df["Timestamp"] >= max_date]

    now = datetime.now()

    if now.strftime("%d") == 1:
        response = requests.get(url, verify=False)
        doc = BeautifulSoup(response.text, "html.parser")
        table = doc.find_all(
            "table",
            {"class": "MsoNormalTable", "style": "width: 1000px; height: 23px;"},
        )
        prev_month_url = url + table[0].find_all("a")[-1]["href"]
        prev_df = extract(prev_month_url)
        df = pd.concat([df, prev_df], axis=0)

    temp_df = df.copy(deep=True)

    try:
        temp_df = pd.concat([df, phivolcs_df], axis=0)
    except:
        pass

    temp_df["Timestamp"] = pd.to_datetime(
        temp_df.Timestamp, infer_datetime_format=True
    ).dt.strftime("%Y-%m-%dT%I:%M:%S %p")
    temp_df["Date"] = temp_df["Date"].astype(str)
    temp_df = temp_df.fillna("")
    temp_df = temp_df.sort_values(
        ["Year", "DOY", "AMPM", "Hour", "Minute"],
        ascending=[False, False, False, False, False],
    )

    temp_df = temp_df.drop_duplicates(keep='last')

    # define the scope
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    # add credentials to the account
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "./assets/tq-explorer-71721ec4a6da.json", scope
    )

    # authorize the clientsheet
    client = gspread.authorize(creds)

    # get the instance of the Spreadsheet
    sheet = client.open("ph-eq-events")

    # get the first sheet of the Spreadsheet
    sheet_instance = sheet.get_worksheet(0)
    sheet_instance.update([temp_df.columns.values.tolist()] + temp_df.values.tolist())

@st.cache(allow_output_mutation=True, show_spinner=False)
def read_usgs_data():
    # df = pd.read_csv("./assets/usgs-df.csv")
    df = pd.read_csv(
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vSdxYJ7zl_Pgo7k5kHOcrHLmW2T9WF5nptZTVHOTXbUIVQompINuLLshM6uco7gqo_6xLTQzMBGdffH/pub?gid=437124652&single=true&output=csv"
    )
    df.columns = colnames
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True)
    df["DOY"] = pd.DatetimeIndex(df["Timestamp"]).dayofyear
    df["Month"] = pd.DatetimeIndex(df["Timestamp"]).month
    df["Day"] = pd.DatetimeIndex(df["Timestamp"]).day
    df["Year"] = pd.DatetimeIndex(df["Timestamp"]).year
    df["Date"] = pd.DatetimeIndex(df["Timestamp"]).date

    df["Timestamp"] = df["Timestamp"].dt.strftime("%Y-%m-%dT%I:%M:%S %p")
    return df

def update_usgs():
    usgs_df = read_usgs_data()
    max_date = datetime.strftime(usgs_df["Date"].max(), "%Y-%m-%d")
    now = datetime.strftime((datetime.now()), "%Y-%m-%d")
    minlat, maxlat, minlon, maxlon = 2.48, 22.09, 115.64, 129.08

    url = f"https://earthquake.usgs.gov//fdsnws/event/1/query.csv?starttime={max_date}%2000:00:00&endtime={now}%2000:00:00&maxlatitude={maxlat}&minlatitude={minlat}&maxlongitude={maxlon}&minlongitude={minlon}&minmagnitude=1&eventtype=earthquake&orderby=time"

    df = pd.read_csv(url)
    df["DOY"] = pd.DatetimeIndex(df["time"]).dayofyear
    df["Month"] = pd.DatetimeIndex(df["time"]).month
    df["Day"] = pd.DatetimeIndex(df["time"]).day
    df["Year"] = pd.DatetimeIndex(df["time"]).year
    df["Date"] = pd.DatetimeIndex(df["time"]).date

    df.columns = colnames

    temp_df = pd.concat([df, usgs_df], axis=0)
    try:
        df["Timestamp"] = df["Timestamp"].dt.strftime("%Y-%m-%dT%I:%M:%S %p")
    except:
        pass
    temp_df["Date"] = temp_df["Date"].astype(str)
    temp_df = temp_df.fillna("")

    temp_df = temp_df.drop_duplicates(keep='last')
    # temp_df.to_csv("./assets/usgs-df.csv", index=False)

    # define the scope
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    # add credentials to the account
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "./assets/tq-explorer-71721ec4a6da.json", scope
    )

    # authorize the clientsheet
    client = gspread.authorize(creds)

    # get the instance of the Spreadsheet
    sheet = client.open("ph-eq-events")

    # get the first sheet of the Spreadsheet
    sheet_instance = sheet.get_worksheet(1)

    sheet_instance.update([temp_df.columns.values.tolist()] + temp_df.values.tolist())


def geodesic_point_buffer(lat, lon, km):
    # Azimuthal equidistant projection
    aeqd_proj = "+proj=aeqd +lat_0={lat} +lon_0={lon} +x_0=0 +y_0=0"
    project = partial(
        pyproj.transform, pyproj.Proj(aeqd_proj.format(lat=lat, lon=lon)), proj_wgs84
    )
    buf = Point(0, 0).buffer(km * 1000)  # distance in metres
    return transform(project, buf).exterior.coords[:]
