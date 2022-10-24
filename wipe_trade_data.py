import sqlite3 as sql

connection = sql.connect("trade.db")
cursor = connection.cursor()
cursor.execute("DELETE FROM symbol_stats")
connection.commit()