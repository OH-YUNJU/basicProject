use testdb;
CREATE TABLE housing_data (
    oftenplace VARCHAR(255) NOT NULL,
    wantplace VARCHAR(255) NOT NULL,
    time INT NOT NULL,
    less_month_avg INT NOT NULL,
    more_month_avg INT NOT NULL,
    less_year_avg INT NOT NULL,
    more_year_avg INT NOT NULL,
    PRIMARY KEY (wantplace)
);

CREATE TABLE place_coordinates (
    wantplace VARCHAR(255) NOT NULL,
    x FLOAT NOT NULL,
    y FLOAT NOT NULL,
    PRIMARY KEY (wantplace)
);