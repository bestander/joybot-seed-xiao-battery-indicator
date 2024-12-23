import board
import digitalio
import time
print("importing board")

# First try to import bleio, fall back to _bleio if not available
try:
    import bleio
    BLE = bleio
    print("Using bleio")
except ImportError:
    import _bleio
    BLE = _bleio
    print("Using _bleio")

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
seen_addresses = set()  # Keep track of devices we've seen

while True:
    led.value = True
    print("\nStarting scan...")
    
    try:
        # Start scan
        for scan in adapter.start_scan():
            # Only show devices with decent signal strength and non-empty advertisements
            if scan.rssi > -70 and scan.advertisement_bytes:
                addr = ':'.join([hex(i) for i in scan.address.address_bytes])
                
                # Only show each device once per scan cycle
                if addr not in seen_addresses:
                    seen_addresses.add(addr)
                    print("-" * 40)
                    print(f"New device found! RSSI: {scan.rssi} dBm")
                    print(f"Address: {addr}")
                    print(f"Advertisement: {bytes(scan.advertisement_bytes).hex()}")
        
        # Clear seen devices for next scan cycle
        seen_addresses.clear()
        
        # Stop scan after 1 second
        time.sleep(1)
        adapter.stop_scan()
        
    except Exception as e:
        print("Scan error:", str(e))
        try:
            adapter.stop_scan()
        except:
            pass
    
    led.value = False
    time.sleep(2)  # Wait longer between scans
    