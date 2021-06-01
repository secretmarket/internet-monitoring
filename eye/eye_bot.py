import http.server
import socketserver
import requests
import datetime as dt
import atexit
import json
from http import HTTPStatus

with open('./settings.json', 'r') as f:
    SETTINGS = json.load(f)

PORT = 9000
TIMEOUT = 30 # seconds
WEBHOOK_URL = SETTINGS['WEBHOOK_URL']
LAST_UPDATE = dt.datetime.now()
IS_DOWN = False
UP_TIME = dt.datetime.now()


def send_slack_message(text: str):
    print(f'Sending to slack: \"{text}\"')
    requests.post(WEBHOOK_URL, json={"text": text})


def exit_fn():
    send_slack_message(
        f'[Monitoring service ended] | THE EYE ... TIRES--')


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        print(self.path)
        if self.path != '/ping':
            self.send_response(HTTPStatus.NOT_FOUND, message=None)
            self.end_headers()
            return

        global LAST_UPDATE
        global IS_DOWN
        global UP_TIME
        if IS_DOWN:
            IS_DOWN = False
            UP_TIME = dt.datetime.now()
            downtime_length = (dt.datetime.now() - LAST_UPDATE).total_seconds()
            downtime_str = str(dt.timedelta(
                seconds=round(downtime_length)))
            send_slack_message(
                f'[Internet status: UP] | total downtime: {downtime_str}')
        LAST_UPDATE = dt.datetime.now()
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
