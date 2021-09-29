import platform
import socket
import urllib3.connection
import http.server
import socketserver
import requests
import datetime as dt
import atexit
from http import HTTPStatus

with open('./settings.json', 'r') as f:
    SETTINGS = json.load(f)

PORT = 9000
TIMEOUT = 30 # seconds
WEBHOOK_URL = SETTINGS['WEBHOOK_URL']
LAST_UPDATE = dt.datetime.now()
IS_DOWN = False
UP_TIME = dt.datetime.now()

# patch urllib connection so that requests doesn't hang periodically
# https://github.com/psf/requests/issues/3353#issuecomment-722772458
platform_name = platform.system()
orig_connect = urllib3.connection.HTTPConnection.connect
def patch_connect(self):
    orig_connect(self)
    if platform_name == "Linux" or platform_name == "Windows":
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1),
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3),
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5),
    elif platform_name == "Darwin":
        TCP_KEEPALIVE = 0x10
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.sock.setsockopt(socket.IPPROTO_TCP, TCP_KEEPALIVE, 3)
urllib3.connection.HTTPConnection.connect = patch_connect


def send_slack_message(text: str):
    print(f'Sending to slack: \"{text}\"')
    requests.post(WEBHOOK_URL, json={"text": text})


def exit_fn():
    send_slack_message(
        f'[Monitoring service ended] | THE EYE ... TIRES--')


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        global LAST_UPDATE
        global IS_DOWN
        global UP_TIME

        if self.path == '/ping':
            if IS_DOWN:
                IS_DOWN = False
                UP_TIME = dt.datetime.now()
                downtime_length = (dt.datetime.now() - LAST_UPDATE).total_seconds()
                downtime_str = str(dt.timedelta(
                    seconds=round(downtime_length)))
                send_slack_message(
                    f'[Internet status: UP] | total downtime: {downtime_str}')
            LAST_UPDATE = dt.datetime.now()
        elif self.path == '/hold':
            body = json.loads(self.rfile.read(content_len))
            hold_time = body['time']
            LAST_UPDATE = dt.datetime.now()
       else:
            self.send_response(HTTPStatus.NOT_FOUND, message=None)
            self.end_headers()
            return
        self.send_response(HTTPStatus.OK, message=None)
        self.end_headers()


class MyServer(socketserver.TCPServer):
    def service_actions(self):
        global LAST_UPDATE
        global IS_DOWN
        global UP_TIME
        # Check if timeout reached
        is_past_timeout = (
            dt.datetime.now() - LAST_UPDATE).total_seconds() > TIMEOUT
        if (is_past_timeout and not IS_DOWN):
            IS_DOWN = True
            uptime_length = (LAST_UPDATE - UP_TIME).total_seconds()
            uptime_str = str(dt.timedelta(seconds=round(uptime_length)))
            send_slack_message(
                f'[Internet status: DOWN] | total uptime: {uptime_str}')


def main():
    # Create an object of the above class
    handler_object = MyHttpRequestHandler

    socketserver.TCPServer.allow_reuse_address = True
    my_server = MyServer(("", PORT), handler_object)

    atexit.register(exit_fn)

    # Start the server
    send_slack_message(
        f'[Monitoring service started] | THE EYE HAS AWAKENED!')
    my_server.serve_forever()


if __name__ == "__main__":
    main()

