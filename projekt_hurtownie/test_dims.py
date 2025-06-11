df_counties = fetch_county_data()
new_row = {
    'fid': 1,
    'state_fips': 6,
    'county_fips': 75,
    'COUNTYNS': 277302,
    'AFFGEOID': '0500000US06075',
    'GEOID': 6075,
    'county_name': 'San Francisco',
    'LSAD': 6,
    'land_area_sqm': 121485107,
    'water_area_sqm': 479107241,
    'long': -122.44000, # zmiana współrzędnych
    'lat': 37.75000
}

df_counties = pd.concat([df_counties, pd.DataFrame([new_row])], ignore_index=True)
df_counties.to_csv('county_data.csv', index=False)

socio = fetch_census_data(year)
new_row = {
    'Population': 58300, # zmiana populacji
    'Median_Income': 62660
    'Total_Housing_Units': 24170
    'State_FIPS': 1,
    'County_FIPS': 1,
    'year': 2021
}

socio = pd.concat([socio, pd.DataFrame([new_row])], ignore_index=True)
socio.to_csv('socio_data.csv', index=False)
