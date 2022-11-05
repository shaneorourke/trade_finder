import sqlite3 as sql
import os

connection = sql.connect("trade.db")
cursor = connection.cursor()

def get_last_log_entry():
    dir_path = 'Logs'
    for file in sorted(os.listdir(dir_path)):
        path = os.path.join(dir_path, file)
        if os.path.isfile(path):
            with open(path) as logfile:
                for line in (logfile.readlines() [-1:]):
                    last_line = line.split('||')[0].split('::')[0]
    return last_line


def data():
    sql = f'SELECT symbol, screener, interval, status, case when ema20 > ema50 then "UP" else "DOWN" end as Trend  FROM symbol_stats'
    cursor.execute(sql)
    results = cursor.fetchall()
    for row in results:
        symbol, screener, interval, status, trend = row[0], row[1], row[2], row[3], row[4]
        print(f'{get_last_log_entry()} || Symbol:{symbol} || Screener:{screener} || Interval:{interval} || Status:{status} || Trend:{trend}')

if __name__ == "__main__":        
    data()