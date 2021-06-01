import requests
import time
import json


with open('./settings.json', 'r') as f:
    SETTINGS = json.load(f)

#PROM_URL = 'http://localhost:9090/api/v1/query'
EYE_URL = SETTINGS['EYE_URL']
CHECK_INTERVAL = 5


def send_update(value: bool):
    try:
        resp = requests.post(EYE_URL, json={"value": str(value)})
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(e)


def main():
    while True:
        internet_is_up = True
        #ping_result = requests.get(
        #    PROM_URL,
        #    params={'query': 'probe_success{instance="8.8.8.8"}'})
        #if ping_result.ok and ping_result.json()['status'] == 'success':
        #    internet_is_up = (
        #        ping_result.json()['data']['result'][0]['value'][1] == "1")
        send_update(True)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
