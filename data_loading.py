import gzip
import io
import logging
import re
from io import StringIO

import pandas as pd
import requests

# Konfiguracja logowania
logging.basicConfig(
    filename='etl_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


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
    variables = "NAME,DP05_0001E,DP03_0062E,DP04_0001E"
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
        "NAME": "County",
        "DP05_0001E": "Population",
        "DP03_0062E": "Median_Income",
        "DP04_0001E": "Total_Housing_Units",
        "state": "State_FIPS",
        "county": "County_FIPS"
    })

    logging.info(
        f"Successfully combined data from all states for year {year}. Rows: {df.shape[0]}, Columns: {df.shape[1]}")

    return df


def fetch_power_outages_data(year: int) -> pd.DataFrame:
    """
    Fetches power outage data for a specific year from the Figshare repository.
    Returns a DataFrame containing the outage data.
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Figshare API endpoint
    figshare_api_url = f"https://api.figshare.com/v2/articles/24237376/files"

    # Send GET request to Figshare API
    response = requests.get(figshare_api_url)
    if response.status_code != 200:
        logging.error(f"Failed to retrieve file list from Figshare API. Status code: {response.status_code}")
        return pd.DataFrame()

    # Find the file for the specified year
    file_url = None
    for file in response.json():
        if f"eaglei_outages_{year}.csv" in file['name']:
            file_url = file['download_url']
            break

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
        'STATEFP': 'state_code',
        'fips': 'county_fips',
        'name': 'county_name',
        'ALAND': 'land_area_sqm',
        'AWATER': 'water_area_sqm',
        'y': 'lat',
        'x': 'long'
    })
    return df


# df_counties = fetch_county_data()
# print(df_counties)
# print(df_counties.columns)
# socio = fetch_census_data(2020)
# print(socio)
# print(socio.columns)
# outages = fetch_power_outages_data(2014)
# print(outages)
# print(outages.columns)
# weather = fetch_prism_weather_data(2020)
# print(weather)
# print(weather.columns)
# events = fetch_storm_events(2021)
# print(events)
# print(events.columns)
