# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
import time, sqlite3 as sql
import pandas as pd
import socket, os

connection = sql.connect("trade.db")
cursor = connection.cursor()

def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

hostName = get_host_ip()
serverPort = 8080

def get_last_log_entry():
    dir_path = 'Logs'
    for file in sorted(os.listdir(dir_path)):
        path = os.path.join(dir_path, file)
        if os.path.isfile(path):
            with open(path) as logfile:
                for line in (logfile.readlines() [-1:]):
                    last_line = line.split('||')[0].split('::')[0]
    return last_line

def color_values(val):
    color = 'white'
    if val == 'waiting':
        color = 'white'
    if val == 'stock':
        color = 'yellow'
    if val == 'OPEN LONG':
        color = 'green' 
    if val == 'OPEN SHORT':
        color = 'red' 
    return 'background-color: %s' % color

def dataframe():
    sql = f'SELECT symbol, screener, interval, status, buy_or_sell, rsi, stock_k, stock_d, macd, macd_signal FROM symbol_stats'
    sql_query = pd.read_sql_query(sql=sql,con=connection)
    df = pd.DataFrame(sql_query, columns = ['symbol', 'screener', 'interval', 'status', 'buy_or_sell', 'rsi', 'stock_k', 'stock_d', 'macd', 'macd_signal'])
    df = df.drop(df[df['status'] == 'waiting'].index, inplace=False)
    df = df.drop(df[df['status'] == 'stock'].index, inplace=False)
    styled_df = df.style.applymap(color_values)
    data_html = styled_df.to_html()
    #data_html = df.to_html()
    return data_html

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
        self.wfile.write(bytes(f"<p>Last Log:{get_last_log_entry()}</p>","utf-8"))
        self.wfile.write(bytes("<body><meta http-equiv='refresh' content='10' />", "utf-8"))
        self.wfile.write(bytes(f"<p>{dataframe()}</p>", "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))

if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")