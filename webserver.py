# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
import time, sqlite3 as sql
import pandas as pd
import socket

connection = sql.connect("trade.db")
cursor = connection.cursor()

def get_host_ip():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return ip

hostName = get_host_ip()
serverPort = 8080

def dataframe():
    sql = f'SELECT symbol, screener, interval, status, buy_or_sell, rsi, stock_k, stock_d, macd, macd_signal FROM symbol_stats'
    sql_query = pd.read_sql_query(sql=sql,con=connection)
    df = pd.DataFrame(sql_query, columns = ['symbol', 'screener', 'interval', 'status', 'buy_or_sell', 'rsi', 'stock_k', 'stock_d', 'macd', 'macd_signal'])
    data_html = df.to_html()
    return data_html

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
        self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
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