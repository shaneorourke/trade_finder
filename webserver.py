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

def generate_html(dataframe: pd.DataFrame):
    # get the table HTML from the dataframe
    table_html = dataframe.to_html(table_id="table")
    # construct the complete HTML with jQuery Data tables
    # You can disable paging or enable y scrolling on lines 20 and 21 respectively
    html = f"""
    <html>
    <header>
        <link href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css" rel="stylesheet">
    </header>
    <body>
    {table_html}
    <script src="https://code.jquery.com/jquery-3.6.0.slim.min.js" integrity="sha256-u7e5khyithlIdTpu22PHhENmPcRdFiHRjhAuHcs05RI=" crossorigin="anonymous"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
    <script>
        $(document).ready( function () {{
            $('#table').DataTable({{
                paging: true,
                "pageLength": 100,
                "lengthMenu": [ "All", 10, 25, 50, 75, 100 ]
            }});
        }});
    </script>
    </body>
    </html>
    """
    # return the html
    return html

def generate_html_basic(dataframe: pd.DataFrame):
    styled_df = dataframe.style.applymap(color_values)
    data_html = styled_df.to_html()
    #data_html = df.to_html()
    return data_html

def dataframe():
    sql = f'SELECT symbol, screener, interval, status, buy_or_sell, rsi, stock_k, stock_d, macd, macd_signal, ema20, ema50 FROM symbol_stats'
    sql_query = pd.read_sql_query(sql=sql,con=connection)
    #col_list = ['symbol', 'screener', 'interval', 'status', 'buy_or_sell', 'rsi', 'stock_k', 'stock_d', 'macd', 'macd_signal', 'ema20', 'ema50']
    col_list = ['symbol', 'screener', 'interval', 'status', 'buy_or_sell']
    df = pd.DataFrame(sql_query, columns=col_list)
    df = df.drop(df[df['status'] == 'waiting'].index, inplace=False)
    df.sort_values(by='status')
    #df = df.drop(df[df['status'] == 'stock'].index, inplace=False)
    data_html = generate_html(df)
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