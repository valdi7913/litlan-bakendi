CREATE Type Direction as ENUM ('Vertical', 'Horizontal');

CREATE TABLE Crossword(
    id SERIAL PRIMARY KEY,
    date DATE,
    width INTEGER,
    height INTEGER
)

CREATE TABLE Cell(
    crossword_id INTEGER,
    value VARCHAR(1) NOT NULL,
    is_blank BOOL NOT NULL,
    x_coord INTEGER,
    y_coord INTEGER,
    FOREIGN KEY (crossword_id) REFERENCES Crossword(id) ON DELETE CASCADE,
    PRIMARY KEY (crossword_id, x_coord, y_coord)
)

CREATE TABLE Hint(
    crossword_id INTEGER,
    id SERIAL,
    x_coord INTEGER NOT NULL,
    y_coord INTEGER NOT NULL,
    direction Direction NOT NULL,
    text VARCHAR(255) NOT NULL,
    FOREIGN KEY (crossword_id) REFERENCES Crossword(id),
    PRIMARY KEY (crossword_id, id),
    UNIQUE (crossword_id, x_coord, y_coord, direction)
)
