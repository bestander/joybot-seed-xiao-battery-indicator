import time
import board
import digitalio
import _bleio
import struct

# Try to import config
try:
    import config
    TARGET_MAC = config.TARGET_MAC
    print(f"Looking for device with MAC: {TARGET_MAC}")
except (ImportError, AttributeError):
    TARGET_MAC = None
    print("No target MAC configured, scanning for BATTERY device...")

# Create UUIDs first so they're registered
SERVICE_UUID = _bleio.UUID("0000ff00-0000-1000-8000-00805f9b34fb")
CHAR_NOTIFY = _bleio.UUID("0000ff01-0000-1000-8000-00805f9b34fb")
CHAR_WRITE = _bleio.UUID("0000ff02-0000-1000-8000-00805f9b34fb")

# Create a whitelist of UUIDs we want to discover
SERVICE_WHITELIST = [SERVICE_UUID]

def decode_bms_data(data):
    """Decode BMS data packet"""
    if len(data) < 4:
        return
    
    # Check packet header (0xDD)
    if data[0] != 0xDD:
        return
    
    # Decode based on command type
    if data[1] == 0x03:  # Basic info
        if len(data) >= 13:
            voltage = (data[4] << 8 | data[5]) / 100.0
            current = ((data[6] << 8 | data[7]) / 100.0)
            soc = data[10]
            power = voltage * current
            
            print("\n=== Battery Status ===")
            print(f"Voltage: {voltage:.1f}V")
            print(f"Current: {current:.1f}A")
            print(f"Power: {power:.1f}W")
            print(f"SOC: {soc}%")
            print("===================")

def request_bms_data(write_char):
    """Send request for basic info"""
    cmd = bytes([0xDD, 0xA5, 0x03, 0x00, 0xFF, 0xFD, 0x77])
    # Use the raw write method from _bleio.Characteristic
    write_char.value = cmd

# Set up the LED
led = digitalio.DigitalInOut(board.LED_BLUE)
led.direction = digitalio.Direction.OUTPUT

# Initialize BLE
adapter = _bleio.adapter
adapter.enabled = True

print("Starting BLE scan...")

while True:
    led.value = True
    print("\nScanning...")
    
    try:
        for scan in adapter.start_scan():
            addr = ':'.join(['{:02X}'.format(b) for b in scan.address.address_bytes])
            
            if TARGET_MAC and addr == TARGET_MAC:
                print(f"Found target device!")
                adapter.stop_scan()
                
                try:
                    print("Connecting...")
                    connection = adapter.connect(scan.address, timeout=10)
                    print("Connected!")
                    
                    if connection.connected:
                        print("Discovering services with whitelist...")
                        for service in connection.discover_remote_services(SERVICE_WHITELIST):
                            print(f"Found service: {service.uuid}")
                            if service.uuid == SERVICE_UUID:
                                print("Found Battery Service!")
                                
                                # Get characteristics
                                notify_char = None
                                write_char = None
                                
                                for char in service.characteristics:
                                    if char.uuid == CHAR_NOTIFY:
                                        notify_char = char
                                    elif char.uuid == CHAR_WRITE:
                                        write_char = char
                                
                                if notify_char and write_char:
                                    print("Found characteristics!")
                                    
                                    # Enable notifications
                                    notify_char.set_cccd(notify=True)
                                    
                                    # Main communication loop
                                    while connection.connected:
                                        # Request data
                                        request_bms_data(write_char)
                                        
                                        # Wait for and process notification
                                        data = notify_char.value
                                        if data:
                                            print("Received:", [hex(b) for b in data])
                                            decode_bms_data(data)
                                        
                                        time.sleep(2)
                                else:
                                    print("Failed to find characteristics")
                                break
                        else:
                            print("Failed to find battery service")
                    
                except Exception as e:
                    print(f"Connection error: {e}")
                finally:
                    try:
                        connection.disconnect()
                    except:
                        pass
                break
    
    except Exception as e:
        print(f"Scan error: {e}")
        try:
            adapter.stop_scan()
        except:
            pass
    
    led.value = False
    time.sleep(1)