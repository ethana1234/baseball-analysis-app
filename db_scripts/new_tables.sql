-- To not worry about foreign key constraints (everything's getting deleted anyways)
PRAGMA foreign_keys = OFF;

-- Drop the tables entirely
DROP TABLE IF EXISTS Teams;
DROP TABLE IF EXISTS TeamSeason;
DROP TABLE IF EXISTS TeamBattingGame;
DROP TABLE IF EXISTS TeamPitchingGame;
DROP TABLE IF EXISTS TeamBattingSeason;
DROP TABLE IF EXISTS TeamPitchingSeason;
DROP TABLE IF EXISTS Batters;
DROP TABLE IF EXISTS Pitchers;
DROP TABLE IF EXISTS PlayerBattingSeason;
DROP TABLE IF EXISTS PlayerPitchingSeason;

-- Create tables
CREATE TABLE Teams (
    id integer PRIMARY KEY,
    Name string NOT NULL,
    team_code string NOT NULL,
    league string NOT NULL,
    division string NOT NULL
);

CREATE TABLE TeamSeason (
    team_id integer,
    season integer,
    wins integer,
    losses integer,
    PRIMARY KEY (team_id, season),
    FOREIGN KEY(team_id) REFERENCES Teams(id)
);

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
    FOREIGN KEY(team_id) REFERENCES Teams(id)
);

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
    FOREIGN KEY(team_id) REFERENCES Teams(id)
);

CREATE TABLE TeamBattingSeason (
    team_id integer,
    season integer,
    Age real,
    G integer,
    PA integer,
    AB integer,
    R integer,
    H integer,
    "2B" integer,
    "3B" integer,
    HR integer,
    RBI integer,
    SB integer,
    CS integer,
    BB integer,
    SO integer,
    BA real,
    OBP real,
    SLG real,
    OPS real,
    TB integer,
    GDP integer,
    HBP integer,
    SH integer,
    SF integer,
    IBB integer,
    PRIMARY KEY (team_id, season),
    FOREIGN KEY(team_id) REFERENCES Teams(id)
);

CREATE TABLE TeamPitchingSeason (
    team_id integer,
    season integer,
    Age real,
    ERA real,
    G integer,
    GS integer,
    GF integer,
    CG integer,
    SHO integer,
    SV integer,
    IP real,
    H integer,
    R integer,
    ER integer,
    HR integer,
    BB integer,
    IBB integer,
    SO integer,
    HBP integer,
    BK integer,
    WP integer,
    BF integer,
    FIP real,
    WHIP real,
    H9 real,
    HR9 real,
    BB9 real,
    SO9 real,
    PRIMARY KEY (team_id, season),
    FOREIGN KEY(team_id) REFERENCES Teams(id)
);

CREATE TABLE Batters (
    id string PRIMARY KEY,
    Name string,
    Pos string,
    Handedness string
);

CREATE TABLE Pitchers (
    id string PRIMARY KEY,
    Name string,
    Handedness string
);

CREATE TABLE PlayerBattingSeason (
    player_id string,
    season integer,
    team_id integer,
    Age integer,
    G integer,
    PA integer,
    AB integer,
    R integer,
    H integer,
    "2B" integer,
    "3B" integer,
    HR integer,
    RBI integer,
    SB integer,
    CS integer,
    BB integer,
    SO integer,
    BA real,
    OBP real,
    SLG real,
    OPS real,
    TB integer,
    GDP integer,
    HBP integer,
    SH integer,
    SF integer,
    IBB integer,
    PRIMARY KEY (player_id, season, team_id),
    FOREIGN KEY(player_id) REFERENCES Batters(id),
    FOREIGN KEY(team_id) REFERENCES Teams(id)
);

CREATE TABLE PlayerPitchingSeason (
    player_id string,
    season integer,
    team_id integer,
    Age integer,
    wins integer,
    losses integer,
    ERA real,
    G integer,
    GS integer,
    GF integer,
    CG integer,
    SHO integer,
    SV integer,
    IP real,
    H integer,
    R integer,
    ER integer,
    HR integer,
    BB integer,
    IBB integer,
    SO integer,
    HBP integer,
    BK integer,
    WP integer,
    BF integer,
    FIP real,
    WHIP real,
    H9 real,
    HR9 real,
    BB9 real,
    SO9 real,
    PRIMARY KEY (player_id, season, team_id),
    FOREIGN KEY(player_id) REFERENCES Pitchers(id),
    FOREIGN KEY(team_id) REFERENCES Teams(id)
);
-- Turn foreign key constraints back on
PRAGMA foreign_keys = ON;
