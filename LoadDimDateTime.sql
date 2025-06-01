-- Utwórz tabelê DimDateTime
IF OBJECT_ID('dbo.DimDateTime', 'U') IS NOT NULL DROP TABLE dbo.DimDateTime;
GO

CREATE TABLE dbo.DimDateTime (
    datetime_id bigint NOT NULL PRIMARY KEY,
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
    year int NOT NULL,
    full_datetime datetime NOT NULL,
    time time(3) NOT NULL,
    hour smallint NOT NULL,
    minute smallint NOT NULL
);
GO

-- Wstaw dane od 2024-01-01 00:00 do 2024-12-31 23:45 co 15 minut
DECLARE @currentDateTime DATETIME = '2024-01-01 00:00:00';
DECLARE @endDateTime DATETIME = '2024-12-31 23:45:00';

WHILE @currentDateTime <= @endDateTime
BEGIN
    DECLARE @date DATE = CAST(@currentDateTime AS DATE);
    DECLARE @year INT = YEAR(@currentDateTime);
    DECLARE @month INT = MONTH(@currentDateTime);
    DECLARE @day INT = DAY(@currentDateTime);
    DECLARE @weekday INT = DATEPART(WEEKDAY, @currentDateTime) - 1;
    DECLARE @weekday_name VARCHAR(10) = DATENAME(WEEKDAY, @currentDateTime);
    DECLARE @is_weekend BIT = CASE WHEN @weekday IN (1, 7) THEN 1 ELSE 0 END;
    DECLARE @day_of_year INT = DATEPART(DAYOFYEAR, @currentDateTime);
    DECLARE @week_of_year INT = DATEPART(WEEK, @currentDateTime);
    DECLARE @iso_week_of_year INT = DATEPART(ISO_WEEK, @currentDateTime);
    DECLARE @month_name VARCHAR(10) = DATENAME(MONTH, @currentDateTime);
    DECLARE @quarter INT = DATEPART(QUARTER, @currentDateTime);
    DECLARE @quarter_name VARCHAR(6) = CASE 
                                            WHEN @quarter = 1 THEN 'First'
                                            WHEN @quarter = 2 THEN 'Second'
                                            WHEN @quarter = 3 THEN 'Third'
                                            ELSE 'Fourth'
                                        END;
    DECLARE @hour SMALLINT = DATEPART(HOUR, @currentDateTime);
    DECLARE @minute SMALLINT = DATEPART(MINUTE, @currentDateTime);
    DECLARE @time TIME = CAST(@currentDateTime AS TIME);
    DECLARE @datetime_id BIGINT = CAST(CONVERT(CHAR(8), @date, 112) + RIGHT('00' + CAST(@hour AS VARCHAR), 2) + RIGHT('00' + CAST(@minute AS VARCHAR), 2) AS BIGINT);
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

    INSERT INTO dbo.DimDateTime (
        datetime_id, full_date, day, day_abbr, weekday, weekday_name,
        is_weekend, is_holiday, day_of_month, day_of_year, week_of_month,
        week_of_year, ISO_week_of_year, month, month_name, quarter,
        quarter_name, year, full_datetime, time, hour, minute
    )
    VALUES (
        @datetime_id, @date, @day, @day_abbr, @weekday, @weekday_name,
        @is_weekend, @is_holiday, @day, @day_of_year, @week_of_month,
        @week_of_year, @iso_week_of_year, @month, @month_name, @quarter,
        @quarter_name, @year, @currentDateTime, @time, @hour, @minute
    );

    -- PrzejdŸ do nastêpnego przedzia³u 15-minutowego
    SET @currentDateTime = DATEADD(MINUTE, 15, @currentDateTime);
END;

