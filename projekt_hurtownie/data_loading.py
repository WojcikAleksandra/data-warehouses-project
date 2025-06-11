import gzip
import io
import logging
import re
from sqlalchemy import create_engine
from io import StringIO

import pandas as pd
import requests

# Konfiguracja logowania
logging.basicConfig(
    filename='etl_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

import sys

if len(sys.argv) < 2:
    print("Brak argumentu roku. Użycie: python data_loading.py <rok>")
    sys.exit(1)

try:
    year = int(sys.argv[1])
except ValueError:
    print("Nieprawidłowy format roku. Rok musi być liczbą całkowitą.")
    sys.exit(1)


def fetch_census_data(year: int) -> pd.DataFrame:
    """
    Fetches data from the American Community Survey (ACS) for a given year
    via the U.S. Census API for all valid U.S. states.

    Parameters:
        year (int): Rok, z którego mają zostać pobrane dane, np. 2022

    Returns:
        pd.DataFrame: Dane dla wszystkich powiatów z populacją, dochodem i mieszkaniami.
    """
    logging.info(f"Starting data fetch from Census API for year {year}")

    valid_state_fips = [f"{i:02d}" for i in range(1, 57) if i not in {3, 7, 14, 43, 52}]
    variables = "DP05_0001E,DP03_0062E,DP04_0001E"
    url = f"https://api.census.gov/data/{year}/acs/acs5/profile"

    all_data = []

    for state_fips in valid_state_fips:
        params = {
            "get": variables,
            "for": "county:*",
            "in": f"state:{state_fips}"
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            df_state = pd.DataFrame(data[1:], columns=data[0])

            # Convert columns to numeric
            df_state["DP05_0001E"] = pd.to_numeric(df_state["DP05_0001E"], errors="coerce")
            df_state["DP03_0062E"] = pd.to_numeric(df_state["DP03_0062E"], errors="coerce")
            df_state["DP04_0001E"] = pd.to_numeric(df_state["DP04_0001E"], errors="coerce")

            all_data.append(df_state)
            logging.info(f"Fetched data for state {state_fips}, number of records: {len(df_state)}")

        except Exception as e:
            logging.error(f"Error while fetching data for state {state_fips} in year {year}: {e}")

    if not all_data:
        logging.critical(f"No data could be fetched from the API for year {year}.")
        raise ValueError(f"No data retrieved for year {year}.")

    df = pd.concat(all_data, ignore_index=True)

    # Rename columns for readability
    df = df.rename(columns={
        "DP05_0001E": "Population",
        "DP03_0062E": "Median_Income",
        "DP04_0001E": "Total_Housing_Units",
        "state": "State_FIPS",
        "county": "County_FIPS"
    })

    logging.info(
        f"Successfully combined data from all states for year {year}. Rows: {df.shape[0]}, Columns: {df.shape[1]}")

    df["year"] = year
    return df


def fetch_power_outages_data(year: int) -> pd.DataFrame:
    """
    Fetches power outage data for a specific year from the Figshare repository.
    Returns a DataFrame containing the outage data.
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    file_url = None
    page = 1
    while True:
        figshare_api_url = f"https://api.figshare.com/v2/articles/24237376/files?page={page}"
        response = requests.get(figshare_api_url)
        if response.status_code != 200:
            logging.error(f"Failed to retrieve files from Figshare API, page {page}. Status code: {response.status_code}")
            break
        files = response.json()
        if not files:
            break

        for file in files:
            logging.info(f"Found file: {file['name']}")
            if f"eaglei_outages_{year}.csv" in file['name']:
                file_url = file['download_url']
                break

        if file_url:
            break 

        page += 1

    if not file_url:
        logging.error(f"File for year {year} not found.")
        return pd.DataFrame()

    # Download the CSV file
    file_response = requests.get(file_url)
    if file_response.status_code != 200:
        logging.error(f"Failed to download file for year {year}. Status code: {file_response.status_code}")
        return pd.DataFrame()

    # Read the CSV data into a DataFrame
    try:
        df = pd.read_csv(StringIO(file_response.text))
        logging.info(f"Successfully fetched data for year {year}.")
    except Exception as e:
        logging.error(f"Error reading CSV data for year {year}: {e}")
        return pd.DataFrame()

    return df


def fetch_prism_weather_data(year: int) -> pd.DataFrame:
    """
    Fetch daily county-level weather data (tmin, tmax, tavg, ppt, stability)
    from the PRISM dataset for all counties in the USA for a given year.

    Parameters:
        year (int): The year for which to download data.

    Returns:
        pd.DataFrame: Combined weather data for all counties.
    """
    base_url = "https://files.asmith.ucdavis.edu/weather/daily/county_noweight/"
    months = [f"{m:02d}" for m in range(1, 13)]
    dfs = []

    logging.info(f"Starting PRISM weather data fetch for year {year}.")

    for month in months:
        yyyymm = f"{year}{month}"
        url = f"{base_url}{yyyymm}.csv"

        try:
            df = pd.read_csv(url)
            df['year'] = year
            df['month'] = int(month)
            dfs.append(df)
            logging.info(f"Successfully fetched data for {yyyymm}. Rows: {df.shape[0]}")
        except Exception as e:
            logging.warning(f"Failed to fetch data for {yyyymm}: {e}")

    if dfs:
        result = pd.concat(dfs, ignore_index=True)
        logging.info(f"Finished PRISM fetch for {year}. Total rows: {result.shape[0]}, columns: {result.shape[1]}")
        return result
    else:
        logging.error(f"No data available to return for year {year}.")
        return pd.DataFrame()


def fetch_storm_events(year: int, data_type: str = 'details') -> pd.DataFrame:
    """
    Fetches weather event data from the NOAA Storm Events Database for the specified year and data type.

    Args:
        year (int): Year, e.g., 2021
        data_type (str): Type of data ('details', 'fatalities', 'locations')

    Returns:
        pd.DataFrame: Table of weather event data
    """
    base_url = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
    logging.info(f"Starting NOAA data fetch: year={year}, data_type={data_type}")

    try:
        resp = requests.get(base_url)
        resp.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to fetch file list from NOAA server: {e}")
        raise

    # Search for matching file
    pattern = re.compile(f"StormEvents_{data_type}-ftp_v1.0_d{year}_c[0-9]+\\.csv\\.gz")
    matches = pattern.findall(resp.text)
    if not matches:
        msg = f"No matching file found for year {year} and data type '{data_type}'"
        logging.error(msg)
        raise ValueError(msg)

    filename = matches[-1]  # Use the latest available file
    file_url = base_url + filename
    logging.info(f"Downloading file: {filename} from {file_url}")

    try:
        response = requests.get(file_url)
        response.raise_for_status()

        with gzip.open(io.BytesIO(response.content), 'rt') as f:
            df = pd.read_csv(f)

        logging.info(f"File {filename} downloaded and loaded. Rows: {df.shape[0]}, Columns: {df.shape[1]}")
        cols = ['INJURIES_DIRECT', 'INJURIES_INDIRECT', 'DEATHS_DIRECT', 'DEATHS_INDIRECT']
        for col in cols:
            df[col] = (df[col].astype(str).str.replace(r'\D', '', regex=True))      
            df[col] = pd.to_numeric(df[col], errors='coerce').astype(int)
        df['MAGNITUDE'] = pd.to_numeric(df['MAGNITUDE'], errors='coerce')
        df['MAGNITUDE'] = df['MAGNITUDE'].round().astype('Int16')
        df.insert(0, 'id', range(1, len(df) + 1))

        df['DAMAGE_PROPERTY'] = df['DAMAGE_PROPERTY'].astype(str).str.strip().str.upper()
        mask_k = df['DAMAGE_PROPERTY'].str.endswith('K', na=False)
        df.loc[mask_k, 'DAMAGE_PROPERTY'] = (
            df.loc[mask_k, 'DAMAGE_PROPERTY'].str.replace('K', '', regex=False).astype(float) * 1_000
        )
        mask_m = df['DAMAGE_PROPERTY'].str.endswith('M', na=False)
        df.loc[mask_m, 'DAMAGE_PROPERTY'] = (
            df.loc[mask_m, 'DAMAGE_PROPERTY'].str.replace('M', '', regex=False).astype(float) * 1_000_000
        )
        df['DAMAGE_PROPERTY'] = pd.to_numeric(df['DAMAGE_PROPERTY'], errors='coerce').round().astype('Int64')

        df['DAMAGE_CROPS'] = df['DAMAGE_CROPS'].astype(str).str.strip().str.upper()
        mask_k = df['DAMAGE_CROPS'].str.endswith('K', na=False)
        df.loc[mask_k, 'DAMAGE_CROPS'] = (
            df.loc[mask_k, 'DAMAGE_CROPS'].str.replace('K', '', regex=False).astype(float) * 1_000
        )
        mask_m = df['DAMAGE_CROPS'].str.endswith('M', na=False)
        df.loc[mask_m, 'DAMAGE_CROPS'] = (
            df.loc[mask_m, 'DAMAGE_CROPS'].str.replace('M', '', regex=False).astype(float) * 1_000_000
        )
        df['DAMAGE_CROPS'] = pd.to_numeric(df['DAMAGE_CROPS'], errors='coerce').round().astype('Int64')

        server = 'DESKTOP-EU3CAMF'
        database = 'PowerOutages_staging_db'
        username = 'sa'
        password = 'loginAAW16!'
        connection_string = (
            f"mssql+pyodbc://{username}:{password}@{server}/{database}"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        )
        engine = create_engine(connection_string)
        df[['id', 'INJURIES_DIRECT', 'INJURIES_INDIRECT', 'DEATHS_DIRECT', 'DEATHS_INDIRECT', 'MAGNITUDE', 'DAMAGE_CROPS', 'DAMAGE_PROPERTY']].to_sql('StormEvents', con=engine, if_exists='append', index=False)

        return df

    except Exception as e:
        logging.error(f"Error during download or loading of file {filename}: {e}")
        raise


def fetch_county_data() -> pd.DataFrame:
    """
    Fetch county-level data for all US counties including:
    FIPS, county name, state name, state code, state abbreviation, latitude, longitude.

    Returns:
        pd.DataFrame: Table of county data
    """
    url = "https://raw.githubusercontent.com/davidingold/county_centroids/master/county_centroids.csv"
    df = pd.read_csv(url)


    df = df.rename(columns={
        'STATEFP': 'state_fips',
        'COUNTYFP': 'county_fips',
        'NAME': 'county_name',
        'ALAND': 'land_area_sqm',
        'AWATER': 'water_area_sqm',
        'y': 'lat',
        'x': 'long'
    })
    return df


df_counties = fetch_county_data()
# print(df_counties)
# print(df_counties.columns)
df_counties.to_csv('county_data.csv', index=False)

socio = fetch_census_data(year)
# print(socio)
# print(socio.columns)
socio.to_csv('socio_data.csv', index=False)

outages = fetch_power_outages_data(year)
# print(outages)
# print(outages.columns)
outages.to_csv('outages_data.csv', index=False)

weather = fetch_prism_weather_data(year)
# print(weather)
# print(weather.columns)
weather.to_csv('weather_data.csv', index=False)

events = fetch_storm_events(year)
# print(events)
# print(events.columns)
events.to_csv('storm_events.csv', index=False)
