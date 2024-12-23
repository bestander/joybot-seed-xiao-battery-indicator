import board
import digitalio
import time
try:
    import config
    TARGET_MAC = config.TARGET_MAC
    print(f"Looking for device with MAC: {TARGET_MAC}")
except (ImportError, AttributeError):
    TARGET_MAC = None
    print("No target MAC configured, scanning for ENJOYBOT device...")

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
    names = []
    
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
        
        # Type 0x08: Shortened Local Name
        elif type_id == 0x08:
            try:
                names.append(bytes(value).decode('utf-8'))
            except:
                pass
                
        # Type 0x09: Complete Local Name
        elif type_id == 0x09:
            try:
                names.append(bytes(value).decode('utf-8'))
            except:
                pass
        
        i += length + 1
    
    return services, names

# Set up the LED
led = digitalio.DigitalInOut(board.LED_BLUE)
led.direction = digitalio.Direction.OUTPUT

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
                
                # If we have a target MAC, only process that device
                if TARGET_MAC and addr == TARGET_MAC:
                    print("-" * 40)
                    print(f"Target device found!")
                    print(f"Address: {addr}")
                    print(f"RSSI: {scan.rssi} dBm")
                    if scan.advertisement_bytes:
                        print(f"Advertisement: {bytes(scan.advertisement_bytes).hex()}")
                    print()
                    
                # If no target MAC, look for devices by service and name
                elif not TARGET_MAC and scan.advertisement_bytes:
                    adv_bytes = bytes(scan.advertisement_bytes)
                    services, names = parse_advertisement(adv_bytes)
                    
                    # Check for our target services
                    if (0xFF00 in services or 0x180A in services):
                        print("-" * 40)
                        print(f"Found interesting device!")
                        print(f"Address: {addr}")
                        print(f"RSSI: {scan.rssi} dBm")
                        print(f"Services: {[hex(s) for s in services]}")
                        if names:
                            print(f"Device names: {names}")
                        
                        # Print raw data for debugging
                        print(f"Raw advertisement: {adv_bytes.hex()}")
                        
                        if 0xFF00 in services:
                            print("Has FF00 (Custom) Service")
                        if 0x180A in services:
                            print("Has 180A (Device Information) Service")
                        
                        if any('ENJOYBOT' in name for name in names):
                            print("*** FOUND ENJOYBOT DEVICE! ***")
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