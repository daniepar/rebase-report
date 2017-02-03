def connect(db, as_dict=False):
    connection = sqlite3.connect(db)
    connection.text_factory = str
    if as_dict:
        connection.row_factory = sqlite3.Row
    return (connection, connection.cursor())
