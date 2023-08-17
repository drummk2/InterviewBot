import sqlite3


connection = sqlite3.connect('InterviewBot.db')

with open('../sql/schema.sql') as schema:
    connection.executescript(schema.read())

connection.commit()
connection.close()