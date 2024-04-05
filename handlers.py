import asyncio
import logging
from bleak import BleakScanner, BleakClient

# Event to watch for new data
battery_level_event = asyncio.Event()
battery_voltage_event = asyncio.Event()

# Global to resources
battery_level_value = 0
battery_voltage_value = 0

log = logging.getLogger('handlers')

# easy setter for globals
def change_battery_level(new_value):
    global battery_level_value
    battery_level_value = new_value

def change_battery_voltage(new_value):
    global battery_voltage_value
    battery_voltage_value = new_value

cancel_observe_3411_0_1 = False
cancel_observe_3411_0_3 = False

async def read_ble():
    global cancel_observe_3411_0_1, cancel_observe_3411_0_3
    devices = await BleakScanner.discover()
    device = next((d for d in devices if d.name == "BLE Battery Demo"), None)
    if device:
        async with BleakClient(device) as client:
            # Function to listen for notify from BLE device
            def b_level_notification_handler(sender, data):
                reading_decimal = int.from_bytes(data, byteorder="little")
                change_battery_level(reading_decimal)
                battery_level_event.set()

            def b_voltage_notification_handler(sender, data):
                reading_decimal = int.from_bytes(data, byteorder="little")
                change_battery_voltage(reading_decimal / 1000.0)
                battery_voltage_event.set()

            # Set up notification handlers
            await client.start_notify("00002A19-0000-1000-8000-00805F9B34FB", b_level_notification_handler)
            await client.start_notify("347BA623-F41A-4B59-A508-DE45079B4F20", b_voltage_notification_handler)

            # Wait for cancellation
            while not cancel_observe_3411_0_1 and not cancel_observe_3411_0_3:
                await asyncio.sleep(5)

            # Stop notifications when cancelled
            await client.stop_notify("00002A19-0000-1000-8000-00805F9B34FB")
            await client.stop_notify("347BA623-F41A-4B59-A508-DE45079B4F20")

    else:
        print("BLE device not found")

asyncio.ensure_future(read_ble())

async def get_battery_level(model, notifier):
    while True:
        global battery_level_value
        await battery_level_event.wait()
        battery_level_event.clear()
        print("New value for resource 1 = ", battery_level_value)
        model.set_resource('3411', '0', "1", battery_level_value)
        notifier()

async def get_battery_voltage(model, notifier):
    while True:
        await asyncio.sleep(1)
        global battery_voltage_value
        await battery_voltage_event.wait()
        battery_voltage_event.clear()
        print("New value for resource 3 = ", battery_voltage_value)
        model.set_resource('3411', '0', "3", battery_voltage_value)
        notifier()


def observe_3411_0_1(*args, **kwargs):
    global cancel_observe_3411_0_1
    log.info(f'observe_3411_0_1(): {args}, {kwargs}')
    model = kwargs['model']
    notifier = kwargs['notifier']
    cancel_observe_3411_0_1 = kwargs['cancel']

    asyncio.ensure_future(get_battery_level(model, notifier))

def observe_3411_0_3(*args, **kwargs):
    global cancel_observe_3411_0_3
    log.info(f'observe_3411_0_3(): {args}, {kwargs}')
    model = kwargs['model']
    notifier = kwargs['notifier']
    cancel_observe_3411_0_3 = kwargs['cancel']

    asyncio.ensure_future(get_battery_voltage(model, notifier))

def observe_3411(*args, **kwargs):
    global cancel_observe_3411_0_3
    log.info(f'observe_3411_0_3(): {args}, {kwargs}')
    model = kwargs['model']
    notifier = kwargs['notifier']
    cancel_observe_3411_0_3 = kwargs['cancel']
    model.set_resource('3411', '0', "1", "1")
    model.set_resource('3411', '0', "3", "3")
