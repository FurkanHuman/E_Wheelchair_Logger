import machine
import time
import uasyncio


class OnBoardLed:
    def __init__(self):
        self.led = machine.Pin('LED', machine.Pin.OUT)

    @staticmethod
    def process_led_state(state):
        led = machine.Pin('LED', machine.Pin.OUT)
        if state == 1:
            led.high()
        elif state == 0:
            led.low()
        elif state == 2:
            led.toggle()
        del led

    def first_up(self):
        self.led.low()
        time.sleep_ms(70)
        self.led.high()
        time.sleep_ms(70)
        self.led.low()

    def blink_eq(self, ms):
        uasyncio.sleep_ms(ms)
        self.led.high()
        uasyncio.sleep_ms(ms)
        self.led.low()

    async def short_up(self, ms):
        uasyncio.sleep_ms(int((ms/6)))
        self.led.high()
        uasyncio.sleep_ms(ms)
        self.led.low()

    async def short_down(self, ms):
        uasyncio.sleep_ms(ms)
        self.led.high()
        uasyncio.sleep_ms(int((ms/6)))
        self.led.low()

    async def long_up(self, ms):
        uasyncio.sleep_ms(int(ms*6))
        self.led.high()
        uasyncio.sleep_ms(ms)
        self.led.low()

    async def long_down(self, ms):
        uasyncio.sleep_ms(ms)
        self.led.high()
        uasyncio.sleep_ms(int(ms*6))
        self.led.low()
