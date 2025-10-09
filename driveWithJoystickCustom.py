import pygame
import sys
import math
import time
from spherov2 import scanner
from spherov2.types import Color
from spherov2.sphero_edu import SpheroEduAPI
from spherov2.commands.power import Power

# ----------------------------
# CONFIG
# ----------------------------
DEADZONE = 0.1
FPS = 60
BATTERY_CHECK_INTERVAL = 30  # seconds

# ----------------------------
# Pygame Joystick Initialization
# ----------------------------
pygame.init()
pygame.joystick.init()

joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
for joy in joysticks:
    print(f"🎮 Joystick detected: {joy.get_name()}")

if not joysticks:
    print("❌ No controller detected.")
    sys.exit(1)

# ----------------------------
# Sphero Initialization
# ----------------------------
toy_name = input("Enter Sphero toy name (e.g. SB-XXXX, or press Enter for auto): ").strip()
print("🔍 Searching for Sphero...")
toy = scanner.find_toy(toy_name=toy_name or None)
if not toy:
    print("❌ Could not find any Sphero.")
    sys.exit(1)

print(f"🔗 Connecting to {toy.name}...")
with SpheroEduAPI(toy) as api:
    print(f"✅ Connected to {toy.name}")

    api.set_front_led(Color(0, 255, 0))  # Green = ready

    # ----------------------------
    # Helper Functions
    # ----------------------------
    def get_battery_level():
        try:
            return Power.get_battery_voltage(toy)
        except Exception as e:
            print(f"[Battery] Check failed: {e}")
            return None

    def set_speed_color(speed):
        if speed == 50:
            api.set_matrix_character("1", Color(255, 200, 0))
        elif speed == 70:
            api.set_matrix_character("2", Color(255, 100, 0))
        elif speed == 100:
            api.set_matrix_character("3", Color(255, 50, 0))
        elif speed == 200:
            api.set_matrix_character("4", Color(255, 0, 0))

    # ----------------------------
    # Control Variables
    # ----------------------------
    angle = 0
    angle_offset = 0
    speed = 50
    last_battery_time = time.time()
    clock = pygame.time.Clock()

    # ----------------------------
    # Main Loop
    # ----------------------------
    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt
                if event.type == pygame.JOYDEVICEADDED:
                    joy = pygame.joystick.Joystick(event.device_index)
                    joysticks.append(joy)
                    print(f"🎮 Controller added: {joy.get_name()}")
                if event.type == pygame.JOYDEVICEREMOVED:
                    joysticks = [j for j in joysticks if j.get_instance_id() != event.instance_id]
                    print(f"❌ Controller removed. Remaining: {len(joysticks)}")

            if not joysticks:
                api.set_speed(0)
                clock.tick(FPS)
                continue

            joystick = joysticks[0]

            # Axis values
            x_axis = joystick.get_axis(0)
            y_axis = joystick.get_axis(1)

            # Shoulder buttons for calibration
            button4=joystick.get_button(4)
            button5=joystick.get_button(5)

            if button4:
                angle_offset += 2
                angle += 2
            if button5:
                angle_offset -= 2
                angle -= 2

            # Speed tier buttons
            if joystick.get_button(0):  # A
                speed = 50
                set_speed_color(speed)
            if joystick.get_button(1):  # B
                speed = 70
                set_speed_color(speed)
            if joystick.get_button(2):  # X
                speed = 100
                set_speed_color(speed)
            if joystick.get_button(3):  # Y
                speed = 200
                set_speed_color(speed)

            # Calculate stick strength
            strength = math.sqrt(x_axis ** 2 + y_axis ** 2)
            if strength < DEADZONE:
                strength = 0.0

            if strength > 0:
                x_axis_fixed = x_axis  # flip left/right for NACON/Xbox
                y_axis_fixed = y_axis
                heading = int((math.degrees(math.atan2(-y_axis_fixed, x_axis_fixed)) + angle_offset) % 360)
                api._SpheroEduAPI__heading = heading
                api.set_heading(heading)
                api.set_speed(speed)
            else:
                api.set_speed(0)

            # Battery check every interval
            if time.time() - last_battery_time >= BATTERY_CHECK_INTERVAL:
                voltage = get_battery_level()
                if voltage:
                    print(f"[Battery] {voltage:.2f} V")
                last_battery_time = time.time()

            clock.tick(FPS)

    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    finally:
        api.set_speed(0)
        pygame.quit()
