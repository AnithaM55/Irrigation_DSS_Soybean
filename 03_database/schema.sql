-- Irrigation DSS Database Schema
-- SQLite / DB Browser compatible
-- Project: Irrigation_DSS_Soybean
-- Author: AnithaM55
-- Date: 2026-04-12

DROP TABLE IF EXISTS IrrigationOutput;
DROP TABLE IF EXISTS WaterBalance;
DROP TABLE IF EXISTS DynamicKc;
DROP TABLE IF EXISTS MOD16_ET;
DROP TABLE IF EXISTS OpenET_ET;
DROP TABLE IF EXISTS WeatherET0;
DROP TABLE IF EXISTS CropStage;
DROP TABLE IF EXISTS GrowingSeason;
DROP TABLE IF EXISTS Station;

CREATE TABLE IF NOT EXISTS Station (
    station_id   VARCHAR(20) NOT NULL,
    name         VARCHAR(60) NOT NULL,
    latitude     REAL        NOT NULL,
    longitude    REAL        NOT NULL,
    state        VARCHAR(30),
    data_source  VARCHAR(30),
    PRIMARY KEY (station_id)
);

CREATE TABLE IF NOT EXISTS GrowingSeason (
    season_id      INTEGER     NOT NULL,
    station_id     VARCHAR(20) NOT NULL,
    year           INTEGER     NOT NULL,
    crop           VARCHAR(30) NOT NULL DEFAULT 'Soybean',
    planting_date  TEXT,
    harvest_date   TEXT,
    notes          TEXT,
    PRIMARY KEY (season_id),
    FOREIGN KEY (station_id) REFERENCES Station(station_id)
);

CREATE TABLE IF NOT EXISTS CropStage (
    stage_id       INTEGER     NOT NULL,
    season_id      INTEGER     NOT NULL,
    growth_stage   VARCHAR(30) NOT NULL,
    stage_start    TEXT,
    stage_end      TEXT,
    Kc_standard    REAL,
    PRIMARY KEY (stage_id),
    FOREIGN KEY (season_id) REFERENCES GrowingSeason(season_id)
);

CREATE TABLE IF NOT EXISTS WeatherET0 (
    et0_id      INTEGER NOT NULL,
    season_id   INTEGER NOT NULL,
    date        TEXT    NOT NULL,
    Tmax_C      REAL,
    Tmin_C      REAL,
    RH_pct      REAL,
    solar_rad   REAL,
    wind_speed  REAL,
    precip_mm   REAL,
    ET0_mm      REAL,
    PRIMARY KEY (et0_id),
    FOREIGN KEY (season_id) REFERENCES GrowingSeason(season_id)
);

CREATE TABLE IF NOT EXISTS OpenET_ET (
    openet_id   INTEGER     NOT NULL,
    season_id   INTEGER     NOT NULL,
    date        TEXT        NOT NULL,
    algorithm   VARCHAR(30) NOT NULL,
    ETc_mm_day  REAL,
    pixel_id    VARCHAR(30),
    QC_flag     INTEGER DEFAULT 0,
    PRIMARY KEY (openet_id),
    FOREIGN KEY (season_id) REFERENCES GrowingSeason(season_id)
);

CREATE TABLE IF NOT EXISTS MOD16_ET (
    modis_id      INTEGER     NOT NULL,
    season_id     INTEGER     NOT NULL,
    date_8day     TEXT        NOT NULL,
    pixel_id      VARCHAR(30),
    ETa_mm_8day   REAL,
    QC_flag       INTEGER DEFAULT 0,
    PRIMARY KEY (modis_id),
    FOREIGN KEY (season_id) REFERENCES GrowingSeason(season_id)
);

CREATE TABLE IF NOT EXISTS DynamicKc (
    kc_id         INTEGER     NOT NULL,
    season_id     INTEGER     NOT NULL,
    stage_id      INTEGER,
    date          TEXT        NOT NULL,
    ETc_mm        REAL,
    ET0_mm        REAL,
    Kc_dynamic    REAL,
    Kc_FAO56      REAL,
    growth_stage  VARCHAR(30),
    PRIMARY KEY (kc_id),
    FOREIGN KEY (season_id) REFERENCES GrowingSeason(season_id),
    FOREIGN KEY (stage_id)  REFERENCES CropStage(stage_id)
);

CREATE TABLE IF NOT EXISTS WaterBalance (
    wb_id               INTEGER NOT NULL,
    season_id           INTEGER NOT NULL,
    date                TEXT    NOT NULL,
    precip_mm           REAL,
    irrigation_mm       REAL DEFAULT 0,
    ETc_mm              REAL,
    soil_water_mm       REAL,
    soil_water_deficit  REAL,
    PRIMARY KEY (wb_id),
    FOREIGN KEY (season_id) REFERENCES GrowingSeason(season_id)
);

CREATE TABLE IF NOT EXISTS IrrigationOutput (
    irr_id                     INTEGER     NOT NULL,
    season_id                  INTEGER     NOT NULL,
    date                       TEXT        NOT NULL,
    soil_water_deficit_mm      REAL,
    irrigation_recommended_mm  REAL,
    trigger_rule               VARCHAR(60),
    growth_stage               VARCHAR(30),
    notes                      TEXT,
    PRIMARY KEY (irr_id),
    FOREIGN KEY (season_id) REFERENCES GrowingSeason(season_id)
);

-- Sample insert — Mississippi 2025
INSERT INTO Station VALUES
    ('MS_33N89W','Starkville MS',33.8711,-89.0592,'Mississippi','NASA Power');

INSERT INTO GrowingSeason VALUES
    (1,'MS_33N89W',2025,'Soybean','2025-05-01','2025-10-05',NULL);

INSERT INTO CropStage VALUES
    (1,1,'Initial','2025-05-01','2025-05-20',0.40),
    (2,1,'Development','2025-05-21','2025-06-29',0.78),
    (3,1,'Mid-Season','2025-06-30','2025-08-27',1.15),
    (4,1,'Late-Season','2025-08-28','2025-10-05',0.50);