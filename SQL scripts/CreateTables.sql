-- DimSocioEcon
CREATE TABLE DimSocioEcon (
    id VARCHAR(10) NOT NULL PRIMARY KEY,
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
    state_fips SMALLINT NOT NULL,
	valid_from_date DATETIME NOT NULL,
	valid_to_date DATETIME NOT NULL,
	active_flag CHAR(3) NOT NULL
);

-- FactPowerOutages
CREATE TABLE FactPowerOutages (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    date_id BIGINT NOT NULL,
	time_id TINYINT NOT NULL,
    geo_id INT NOT NULL,
    socioecon_id VARCHAR(10) NOT NULL,
    customers_out INT NOT NULL,
    temp_mean DECIMAL(5,2) NULL,
    temp_max DECIMAL(5,2) NULL,
    temp_min DECIMAL(5,2) NULL,
    precipitation_mm DECIMAL(5,2) NULL,
    FOREIGN KEY (date_id) REFERENCES DimDate(date_id),
	FOREIGN KEY (time_id) REFERENCES DimTime(time_id),
    FOREIGN KEY (geo_id) REFERENCES DimGeo(id),
    FOREIGN KEY (socioecon_id) REFERENCES DimSocioEcon(id)
);

-- FactEvent
CREATE TABLE FactEvent (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    begin_date_id BIGINT NOT NULL,
	begin_time_id TINYINT NOT NULL,
    end_date_id BIGINT NOT NULL,
	end_time_id TINYINT NOT NULL,
    geo_id INT NOT NULL,
    deaths_indirect SMALLINT NULL,
    deaths_direct SMALLINT NULL,
    injuries_indirect SMALLINT NULL,
    injuries_direct SMALLINT NULL,
    damage_crops BIGINT NULL,
    damage_property BIGINT NULL,
    magnitude SMALLINT NULL,
    type VARCHAR(30) NOT NULL,
    FOREIGN KEY (begin_date_id) REFERENCES DimDate(date_id),
	FOREIGN KEY (begin_time_id) REFERENCES DimTime(time_id),
    FOREIGN KEY (end_date_id) REFERENCES DimDate(date_id),
	FOREIGN KEY (end_time_id) REFERENCES DimTime(time_id),
    FOREIGN KEY (geo_id) REFERENCES DimGeo(id)
);
