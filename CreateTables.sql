-- DimSocioEcon
CREATE TABLE DimSocioEcon (
    id INT NOT NULL PRIMARY KEY,
    population BIGINT NOT NULL,
    median_income BIGINT NOT NULL,
    total_housing_units BIGINT NOT NULL,
    land_area_sqm BIGINT NOT NULL,
    year INT NOT NULL
);

-- DimGeo
CREATE TABLE DimGeo (
    id INT NOT NULL PRIMARY KEY,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    county_fips INT NOT NULL,
    county_name VARCHAR(50) NOT NULL,
    state_name VARCHAR(20) NOT NULL,
    state_abbr VARCHAR(2) NOT NULL,
    state_fips SMALLINT NOT NULL
);

-- FactPowerOutages
CREATE TABLE FactPowerOutages (
    id BIGINT NOT NULL PRIMARY KEY,
    datetime_id BIGINT NOT NULL,
    geo_id INT NOT NULL,
    socioecon_id INT NOT NULL,
    customers_out INT NOT NULL,
    temp_mean DECIMAL(5,2) NULL,
    temp_max DECIMAL(5,2) NULL,
    temp_min DECIMAL(5,2) NULL,
    precipitation_mm DECIMAL(5,2) NULL,
    FOREIGN KEY (datetime_id) REFERENCES DimDateTime(datetime_id),
    FOREIGN KEY (geo_id) REFERENCES DimGeo(id),
    FOREIGN KEY (socioecon_id) REFERENCES DimSocioEcon(id)
);

-- FactEvent
CREATE TABLE FactEvent (
    id BIGINT NOT NULL PRIMARY KEY,
    begin_datetime_id BIGINT NOT NULL,
    end_datetime_id BIGINT NOT NULL,
    geo_id INT NOT NULL,
    deaths_indirect SMALLINT NULL,
    deaths_direct SMALLINT NULL,
    injuries_indirect SMALLINT NULL,
    injuries_direct SMALLINT NULL,
    damage_crops BIGINT NULL,
    damage_property BIGINT NULL,
    magnitude SMALLINT NULL,
    type VARCHAR(30) NOT NULL,
    FOREIGN KEY (begin_datetime_id) REFERENCES DimDateTime(datetime_id),
    FOREIGN KEY (end_datetime_id) REFERENCES DimDateTime(datetime_id),
    FOREIGN KEY (geo_id) REFERENCES DimGeo(id)
);
