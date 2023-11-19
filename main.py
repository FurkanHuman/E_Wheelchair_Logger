import machine
import ntptime
import uasyncio
import gc
import time
import binascii
from machine import I2C, Pin
from Lib.myLib.OnBoardLed import OnBoardLed
from Lib.myLib.WConnection import WConnection
from Lib.myLib.OnBoardLed import OnBoardLed
from Lib.myLib.WConnection import WConnection
from Lib.myLib.SDCardHandler import SDCardHandler
from Lib.myLib.SDLogger import SDLogger
from Lib.myLib.SDDataLogger import SDDataLogger
from Lib.Driver.imu import MPU6050, MPUException
from Lib.Driver.ina226 import INA226

# boot and debug start

led = OnBoardLed()

led.first_up()

print(time.localtime())

wifi = WConnection()

scl_1 = Pin(15)
sda_1 = Pin(14)

i2c_1 = I2C(1, scl=scl_1, sda=sda_1, freq=400000)

gps_uart = machine.UART(0, baudrate=19200)

sd0 = SDCardHandler(spi_id=0, sck=6, mosi=7, miso=4, cs=5, baudrate=5000000)

print('Scan i2c_1 bus...')
devices = i2c_1.scan()

if len(devices) == 0:
    print("No I2C devices found!")
else:
    print('I2C devices found:', len(devices))
    for device in devices:
        print("Decimal address: ", device, " | Hex address: ", hex(device))

# boot and debug end

mpu6050_0X68 = MPU6050(side_str=i2c_1)
ina226_0X40 = INA226(i2c_device=i2c_1)

sd0.ls("/sd/")
sd0.current_folder = sd0.create_new_root_folder()
sd0.ls(sd0.current_folder)
sdlog: SDLogger = SDLogger(sd_ch=sd0)



cs: bool = wifi.connect_wifi()

if cs:
    sdlog.c_log("Wifi is connected")

    try:
        ntptime.settime()
        sdlog.c_log("time is updated")
        uasyncio.run(led.short_up(500))

    except OSError as e:
        uasyncio.run(led.long_up(1000))
        sdlog.c_log("time not updated")
        wifi.disconnect_turn_off()
        sdlog.c_log("Wifi turn off")
else:
    sdlog.c_log("wifi is not connected")

gc.enable()
wifi = None

sdlog.c_log("wifi Object is deleted")

sd_data_mpu6050_0x68_log: SDDataLogger = SDDataLogger(
    sd_ch=sd0, file_name="MPU6050_0x68")

sd_data_ina226_0x40_log: SDDataLogger = SDDataLogger(
    sd_ch=sd0, file_name="INA226_0x40")

sd_data_GPS_log: SDDataLogger = SDDataLogger(
    sd_ch=sd0, file_name="GPS_NEO_6M")


async def mpu6050_0x68_loop_async():
    while True:
        try:
            ax = round(mpu6050_0X68.accel.x, 2)
            ay = round(mpu6050_0X68.accel.y, 2)
            az = round(mpu6050_0X68.accel.z, 2)
            gx = round(mpu6050_0X68.gyro.x, 2)
            gy = round(mpu6050_0X68.gyro.y, 2)
            gz = round(mpu6050_0X68.gyro.z, 2)
            temp = round(mpu6050_0X68.temperature, 2)
            await uasyncio.sleep_ms(20)
            ds: str = f"{ax},{ay},{az},{gx},{gy},{gz},{temp}"
            sd_data_mpu6050_0x68_log.log(ds)

        except MPUException as e:
            sdlog.e_log(e=e, comment="MPU6050 0x68 is broken")
        gc.collect()


async def ina226_0x40_loop_async():
    while True:
        try:
            voltage_bus = ina226_0X40.bus_voltage
            voltage_rshunt = ina226_0X40.shunt_voltage
            current = ina226_0X40.current
            power = ina226_0X40.power

            ds: str = f"{voltage_bus},{voltage_rshunt},{current},{power}"+"\r"
            await uasyncio.sleep_ms(20)
            sd_data_ina226_0x40_log.log(ds)
            ds = ""

        except OSError as e:
            sdlog.e_log(e, "ina226 0x40 is broken")
        gc.collect()


async def GPS_loop_async():
    while True:
        try:
            await uasyncio.sleep_ms(200)
            buff: bytes = gps_uart.read()

            if buff:

                buff_str: str = str(
                    buff, 'utf-8').replace('\r\n', '')  # type: ignore
                sd_data_GPS_log.log(data_str=buff_str)
                gps_uart.flush()

        except OSError as e:
            sdlog.e_log(e, "gps is broken")
        gc.collect()


def zda_info_parser(zda_parts: list[str]): # TODO: W.I.P function part 2
    try:

        hhmmss = zda_parts[1].split('.')[0]
        day = int(zda_parts[2])
        month = int(zda_parts[3])
        year = int(zda_parts[4])

        local_zone_hours = int(zda_parts[5])
        local_zone_minutes = int(zda_parts[6].split('*')[0])

        hour = int(hhmmss[:2])
        minute = int(hhmmss[2:4])
        second = int(hhmmss[4:6])
        sub_second = int(zda_parts[1].split('.')[1])*10

        parts_of_zda = (sub_second,
                        second,
                        minute,
                        hour,
                        local_zone_minutes,
                        local_zone_hours,
                        day,
                        month,
                        year)

        return parts_of_zda

    except ValueError as e:
        sdlog.e_log(e, "Type conversion error")


gps_clock_try_count: int = 3


async def update_pico_clock_with_gps_loop(): # TODO: W.I.P function
    try:
        for _ in range(gps_clock_try_count):

            rtc = machine.RTC()

            buff = gps_uart.read()
            if buff:
                buff_str: str = str(buff, 'utf-8') # type: ignore

             buff_gpzda:str = [line for line in buff_str.split('\r\n') if line.startswith("$GPZDA")][0]  # type: ignore

            uasyncio.sleep_ms(500)
            gps_uart.flush()
            print(buff_gpzda)
            # buff_gpzda: str = "$GPZDA,131143.20,24,10,2023,00,00*65"
            zda_parse = zda_info_parser(buff_gpzda.split(','))

            if zda_parse == None:
                return

            rtc.datetime(datetimetuple=[
                zda_parse[8],
                zda_parse[7],
                zda_parse[6],
                0,
                zda_parse[3],
                zda_parse[2],
                zda_parse[1],
                0])
            sdlog.c_log(
                f"GPS Time updated by RTC. RTC Time info [{zda_parse}]. Count By: {gps_clock_try_count}/{_+1}")

            uasyncio.run(led.short_down(500))

    except Exception as e:
        sdlog.e_log(
            e, "GPS Time updated by RTC failed.")
    uasyncio.sleep_ms(3600000)


gc.enable()

loop = uasyncio.new_event_loop()

loop.create_task(GPS_loop_async())
loop.create_task(update_pico_clock_with_gps_loop()) # TODO: W.I.P function part 3

loop.create_task(mpu6050_0x68_loop_async())
loop.create_task(ina226_0x40_loop_async())

loop.run_forever()