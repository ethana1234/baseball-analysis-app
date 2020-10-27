-- To not worry about foreign key constraints (everything's getting deleted anyways)
PRAGMA foreign_keys = OFF;

-- Drop the tables entirely
DROP TABLE IF EXISTS Teams;
DROP TABLE IF EXISTS TeamSeason;
DROP TABLE IF EXISTS TeamPitchingGame;
DROP TABLE IF EXISTS TeamBattingGame;
DROP TABLE IF EXISTS PlayerBattingSeason;
DROP TABLE IF EXISTS PlayerPitchingSeason;

-- Create tables
CREATE TABLE IF NOT EXISTS Teams (
    id integer PRIMARY KEY,
    name string NOT NULL,
    team_code string NOT NULL,
    league string NOT NULL,
    division string NOT NULL);

CREATE TABLE IF NOT EXISTS TeamSeason (
    team_id integer,
    season integer,
    wins integer,
    losses integer,
    PRIMARY KEY (team_id, season),
    FOREIGN KEY(team_id) REFERENCES Teams(id));

CREATE TABLE TeamBattingGame (
    game_id integer,
    team_id integer,
    opp_id integer,
    game_date string,
    season integer,
    HomeAway string,
    OppStarterThr string,
    Result string,
    RunsAgainst integer,
    PA integer,
    AB integer,
    R integer,
    H integer,
    "2B" integer,
    "3B" integer,
    HR integer,
    RBI integer,
    BB integer,
    IBB integer,
    SO integer,
    HBP integer,
    SH integer,
    SF integer,
    ROE integer,
    GDP integer,
    SB integer,
    CS integer,
    LOB integer,
    BA real,
    OBP real,
    SLG real,
    OPS real,
    PRIMARY KEY (game_id, team_id),
    FOREIGN KEY(team_id) REFERENCES Teams(id));

CREATE TABLE TeamPitchingGame (
    game_id integer,
    team_id integer,
    opp_id integer,
    game_date string,
    season integer,
    HomeAway string,
    Result string,
    RunsFor integer,
    H integer,
    R integer,
    ER integer,
    UER integer,
    BB integer,
    SO integer,
    HR integer,
    HBP integer,
    BF integer,
    Pitches integer,
    Strikes integer,
    IR integer,
    "IS" integer,
    SB integer,
    CS integer,
    AB integer,
    "2B" integer,
    "3B" integer,
    IBB integer,
    SH integer,
    SF integer,
    ROE integer,
    GDP integer,
    PitchersUsed integer,
    IP real,
    ERA real,
    PRIMARY KEY (game_id, team_id),
    FOREIGN KEY(team_id) REFERENCES Teams(id));

-- Turn foreign key constraints back on
PRAGMA foreign_keys = ON;
