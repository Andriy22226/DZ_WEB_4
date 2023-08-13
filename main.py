from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import json
import mimetypes
import pathlib
import socket
import threading
import urllib.parse

HOST = "127.0.0.1"
UDP_PORT = 5000
HTTP_PORT = 3000
exit_flag = False
lock = threading.Lock()


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        print(pr_url.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("message.html")
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def send_to_socket(self, data: dict):
        bytes = json.dumps(data).encode()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server = HOST, UDP_PORT
        sock.sendto(bytes, server)
        sock.close()

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {
            key: value for key, value in [el.split("=") for el in data_parse.split("&")]
        }
        print(data_dict)
        self.send_to_socket(data_dict)

        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())


def run_http(ip, port):
    server_address = (ip, port)
    http = HTTPServer(server_address, HttpHandler)
    while not exit_flag:
        http.handle_request()
    http.server_close()


def run_udp(ip, port, data_file):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server = ip, port
    sock.bind(server)
    while not exit_flag:
        data, address = sock.recvfrom(1024)
        data_dict = json.loads(data.decode())
        record = {str(datetime.now()): data_dict}
        with lock:
            data_file.seek(0)
            try:
                messages = json.load(data_file)
            except json.JSONDecodeError:
                messages = {}
            messages.update(record)
            data_file.seek(0)
            json.dump(messages, data_file, ensure_ascii=False)
            data_file.truncate()
    sock.close()


if __name__ == "__main__":
    dir_path = pathlib.Path(".")
    if not pathlib.Path().joinpath("storage/data.json").exists():
        stor_path = dir_path / "storage"
        stor_path.mkdir(parents=True, exist_ok=True)
        data_file = open("storage/data.json", "x", encoding="UTF-8")
    data_file = open("storage/data.json", "r+", encoding="UTF-8")
    udp_server = threading.Thread(
        target=run_udp, args=(HOST, UDP_PORT, data_file))
    http_server = threading.Thread(target=run_http, args=(HOST, HTTP_PORT))
    udp_server.start()
    http_server.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        exit_flag = True
        udp_server.join()
        http_server.join()
        data_file.close()

# Ваша мета реалізувати найпростіший вебзастосунок. За основу взяти наступні файли.

# За аналогією з розглянутим прикладом у конспекті, створіть вебзастосунок з маршрутизацією для двох html сторінок: index.html та message.html.

# Також:

# Обробіть під час роботи застосунку статичні ресурси: style.css, logo.png;
# Організуйте роботу з формою на сторінці message.html;
# У разі виникнення помилки 404 Not Found повертайте сторінку error.html
# Ваш застосунок працює на порту 3000
# Для роботи з формою створіть Socket сервер на порту 5000. Алгоритм роботи такий. Ви вводите дані у форму, вони потрапляють у ваш вебзастосунок, який пересилає його далі на обробку за допомогою socket (протокол UDP) Socket серверу. Socket сервер перетворює отриманий байт-рядок у словник і зберігає його в json файл data.json в папку storage.

# Формат запису файлу data.json наступний:

# {
#   "2022-10-29 20:20:58.020261": {
#     "username": "krabaton",
#     "message": "First message"
#   },
#   "2022-10-29 20:21:11.812177": {
#     "username": "Krabat",
#     "message": "Second message"
#   }
# }

# Де ключ кожного повідомлення - це час отримання повідомлення: datetime.now(). Тобто кожне нове повідомлення від вебзастосунку дописується у файл storage/data.json з часом отримання.

# Використовуйте для створення вашого вебзастосунку один файл main.py. Запустіть HTTP сервер і Socket сервер у різних потоках.
