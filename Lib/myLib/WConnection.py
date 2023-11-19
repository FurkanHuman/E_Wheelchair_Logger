import random
import network
import uasyncio
import time
from .OnBoardLed import OnBoardLed

CONNECTION_FILE = "/Secrets/wireless.csv"


class WConnection:

    def __init__(self):
        self.led = OnBoardLed()
        self._connection_alive = False
        self._ssid = ""
        self._password = ""
        network.country('TR')

    def connect_wifi(self):
        wait = 15
        networks = self.read_wifi_networks()
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)

        for ssid, password in networks:
            self.wlan.connect(ssid, password)
            while wait > 0:
                if not self.wlan.isconnected():
                    print(f"Connecting to Wi-Fi SSID: {ssid}")
                    print('waiting for connection...')
                    uasyncio.run(self.led.short_up(10))
                    time.sleep(1)
                    wait -= 1
                    self._connection_alive = False
                else:
                    self._connection_alive = True
                    self.connected_message()
                    print('Wi-Fi connection successful!')
                    del networks
                    return True
            wait = 15
            print(f"Failed to connect to Wi-Fi SSID: {ssid}")
        print('All Wi-Fi connections failed')
        return False

    def disconnect_turn_off(self):
        if self.wlan.isconnected():
            self.wlan.disconnect
            self.wlan.active(False)

        self.wlan.deinit()

    def access_point(self):
        self.wlan = network.WLAN(network.AP_IF)
        ap = self.wlan
        ap.config(essid="Pi_picoW", password="RPIPicoW")
        ap.active(True)

    async def connection_control(self):
        while True:
            await uasyncio.sleep_ms(10)
            if not self.wlan.isconnected():
                self._connection_alive = False
                await uasyncio.sleep_ms(300)
                print(".")
                await uasyncio.run(self.led.short_up(10))
                self.wlan.connect(self._ssid, self._password)
            else:
                self._connection_alive = True

    def connected_message(self):
        self_ip = self.wlan.ifconfig()[0]
        print(f"Connected to Wi-Fi SSID: {self._ssid}")
        print('network config: ', self_ip)

    def read_wifi_networks(self):
        wifi_networks = []

        try:
            with open(CONNECTION_FILE, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    ssid, password = line.strip().split(',')
                    wifi_networks.append((ssid, password))
        except (OSError):
            self.create_default_connection_file()

        if not wifi_networks:
            self.create_default_connection_file()

        return wifi_networks

    def create_default_connection_file(self):
        with open(CONNECTION_FILE, 'w') as file:
            password = ''.join(random.choice(
                '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(16))
            file.write(f'IOT_AP,{password}\n')
            del file
