import board
import digitalio
import time

# First try to import bleio, fall back to _bleio if not available
try:
    import bleio
    BLE = bleio
    print("Using bleio")
except ImportError:
    import _bleio
    BLE = _bleio
    print("Using _bleio")

def parse_advertisement(data):
    """Parse BLE advertisement data"""
    i = 0
    services = set()
    while i < len(data):
        length = data[i]
        if length == 0:
            break
        
        if i + length + 1 > len(data):
            break
            
        type_id = data[i + 1]
        value = data[i + 2:i + length + 1]
        
        # Type 0x02 or 0x03: 16-bit Service Class UUIDs
        if type_id in (0x02, 0x03) and length >= 3:
            for j in range(0, len(value), 2):
                if j + 1 < len(value):
                    service = (value[j+1] << 8) | value[j]
                    services.add(service)
        
        i += length + 1
    
    return services

# Set up the LED
led = digitalio.DigitalInOut(board.LED_BLUE)
led.direction = digitalio.Direction.OUTPUT

print("Looking for devices with FF00 or 180A services...")

try:
    print("Getting BLE adapter...")
    adapter = BLE.adapter
    print("Enabling adapter...")
    adapter.enabled = True
    print("Adapter enabled successfully")
except Exception as e:
    print("Error initializing BLE:", str(e))
    # Keep the board running to see the error
    while True:
        led.value = True
        time.sleep(0.5)
        led.value = False
        time.sleep(0.5)

print("scanning...")
seen_addresses = set()  # Track devices we've seen

while True:
    led.value = True
    print("\nStarting scan...")
    
    try:
        # Start scan
        for scan in adapter.start_scan():
            addr_bytes = scan.address.address_bytes
            addr = ':'.join(['{:02X}'.format(b) for b in addr_bytes])
            
            if addr not in seen_addresses:
                seen_addresses.add(addr)
                
                if scan.advertisement_bytes:
                    adv_bytes = bytes(scan.advertisement_bytes)
                    services = parse_advertisement(adv_bytes)
                    
                    # Check for our target services
                    if 0xFF00 in services or 0x180A in services:
                        print("-" * 40)
                        print(f"Found interesting device!")
                        print(f"Address: {addr}")
                        print(f"RSSI: {scan.rssi} dBm")
                        print(f"Services: {[hex(s) for s in services]}")
                        
                        if 0xFF00 in services:
                            print("Has FF00 (Custom) Service")
                        if 0x180A in services:
                            print("Has 180A (Device Information) Service")
                        print()
        
        # Clear seen devices and stop scan
        seen_addresses.clear()
        time.sleep(1)
        adapter.stop_scan()
        
    except Exception as e:
        print("Scan error:", str(e))
        try:
            adapter.stop_scan()
        except:
            pass
    
    led.value = False
    time.sleep(1)  # Wait between scans