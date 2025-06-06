IF OBJECT_ID('dbo.DimDate', 'U') IS NOT NULL DROP TABLE dbo.DimDate;
GO

CREATE TABLE dbo.DimDate (
    date_id bigint NOT NULL PRIMARY KEY,
    full_date date NOT NULL,
    day tinyint NOT NULL,
    day_abbr char(2) NOT NULL,
    weekday tinyint NOT NULL,
    weekday_name varchar(10) NOT NULL,
    is_weekend bit NOT NULL,
    is_holiday bit NOT NULL,
    day_of_month tinyint NOT NULL,
    day_of_year smallint NOT NULL,
    week_of_month tinyint NOT NULL,
    week_of_year smallint NOT NULL,
    ISO_week_of_year tinyint NOT NULL,
    month tinyint NOT NULL,
    month_name varchar(10) NOT NULL,
    quarter tinyint NOT NULL,
    quarter_name varchar(6) NOT NULL,
    year int NOT NULL
);
GO

DECLARE @currentDate DATE = '2021-01-01';
DECLARE @endDate DATE = '2030-12-31';

WHILE @currentDate <= @endDate
BEGIN
    DECLARE @date DATE = CAST(@currentDate AS DATE);
    DECLARE @year INT = YEAR(@currentDate);
    DECLARE @month INT = MONTH(@currentDate);
    DECLARE @day INT = DAY(@currentDate);
    DECLARE @weekday INT = DATEPART(WEEKDAY, @currentDate) - 1;
    DECLARE @weekday_name VARCHAR(10) = DATENAME(WEEKDAY, @currentDate);
    DECLARE @is_weekend BIT = CASE WHEN @weekday IN (1, 7) THEN 1 ELSE 0 END;
    DECLARE @day_of_year INT = DATEPART(DAYOFYEAR, @currentDate);
    DECLARE @week_of_year INT = DATEPART(WEEK, @currentDate);
    DECLARE @iso_week_of_year INT = DATEPART(ISO_WEEK, @currentDate);
    DECLARE @month_name VARCHAR(10) = DATENAME(MONTH, @currentDate);
    DECLARE @quarter INT = DATEPART(QUARTER, @currentDate);
    DECLARE @quarter_name VARCHAR(6) = CASE 
                                            WHEN @quarter = 1 THEN 'First'
                                            WHEN @quarter = 2 THEN 'Second'
                                            WHEN @quarter = 3 THEN 'Third'
                                            ELSE 'Fourth'
                                        END;
    DECLARE @date_id BIGINT = CAST(CONVERT(CHAR(8), @date, 112) AS BIGINT);
    DECLARE @is_holiday BIT = 0;
    DECLARE @week_of_month TINYINT = DATEDIFF(WEEK, DATEFROMPARTS(@year, @month, 1), @date) + 1;
    DECLARE @day_abbr CHAR(2) = 
        CASE 
            WHEN @weekday_name = 'Monday' THEN 'Mo'
            WHEN @weekday_name = 'Tuesday' THEN 'Tu'
            WHEN @weekday_name = 'Wednesay' THEN 'We'
            WHEN @weekday_name = 'Thursday' THEN 'Th'
			WHEN @weekday_name = 'Friday' THEN 'Fr'
			WHEN @weekday_name = 'Saturday' THEN 'Sa'
            ELSE 'Su' 
        END;

    INSERT INTO dbo.DimDate (
        date_id, full_date, day, day_abbr, weekday, weekday_name,
        is_weekend, is_holiday, day_of_month, day_of_year, week_of_month,
        week_of_year, ISO_week_of_year, month, month_name, quarter,
        quarter_name, year
    )
    VALUES (
        @date_id, @date, @day, @day_abbr, @weekday, @weekday_name,
        @is_weekend, @is_holiday, @day, @day_of_year, @week_of_month,
        @week_of_year, @iso_week_of_year, @month, @month_name, @quarter,
        @quarter_name, @year
    );

    SET @currentDate = DATEADD(DAY, 1, @currentDate);
END;


IF OBJECT_ID('dbo.DimTime', 'U') IS NOT NULL DROP TABLE dbo.DimTime;
GO

CREATE TABLE dbo.DimTime (
    time_id tinyint NOT NULL PRIMARY KEY,
    time time(3) NOT NULL,
    hour tinyint NOT NULL,
    minute tinyint NOT NULL
);
GO

DECLARE @currentTime DATETIME = '00:00:00';
DECLARE @endTime DATETIME = '23:45:00';
DECLARE @time_id TINYINT = 1;

WHILE @currentTime <= @endTime
BEGIN
    DECLARE @hour TINYINT = DATEPART(HOUR, @currentTime);
    DECLARE @minute TINYINT = DATEPART(MINUTE, @currentTime);

    INSERT INTO dbo.DimTime (
        time_id, time, hour, minute
    )
    VALUES (
        @time_id, @currentTime, @hour, @minute
    );

	SET @time_id += 1;
    SET @currentTime = DATEADD(MINUTE, 15, @currentTime);
END;
