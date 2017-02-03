CREATE TABLE conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commit_sha TEXT,
    parent_sha TEXT,
    stopped_sha TEXT,
    onto_sha TEXT
);

CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conflict_id INTEGER,
    path TEXT,
    resolved TEXT,
    conflict TEXT,
    stopped TEXT,
    onto TEXT,
    status TEXT,
    FOREIGN KEY(conflict_id) REFERENCES conflicts(id)
);

CREATE TABLE tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conflict_id INTEGER,
    team TEXT,
    ticket INTEGER,
    FOREIGN KEY(conflict_id) REFERENCES conflicts(id)
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conflict_id INTEGER,
    text TEXT,
    sha TEXT,
    FOREIGN KEY(conflict_id) REFERENCES conflicts(id)
);
