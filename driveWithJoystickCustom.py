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
ARROW_SIZE = 100
BATTERY_CHECK_INTERVAL = 30  # seconds

# ----------------------------
# Pygame Initialization
# ----------------------------
pygame.init()
pygame.font.init()
pygame.joystick.init()

# Check joystick
if pygame.joystick.get_count() == 0:
    print("No joystick detected.")
    sys.exit(1)

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Joystick initialized: {joystick.get_name()}")

# Screen setup
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Sphero Control + Visualization")
font = pygame.font.Font(None, 24)

# Load arrow image
arrow_image = pygame.image.load("arrow.png")
arrow_image = pygame.transform.scale(arrow_image, (ARROW_SIZE, ARROW_SIZE))
arrow_location = (screen_width / 2, screen_height / 2)

clock = pygame.time.Clock()

# ----------------------------
# Sphero Initialization
# ----------------------------
toy_name = input("Enter Sphero toy name (e.g. SB-XXXX): ").strip()

print("Searching for Sphero...")
toy = scanner.find_toy(toy_name=toy_name)
if not toy:
    print(f"Could not find Sphero with name {toy_name}")
    sys.exit(1)

print(f"Connecting to {toy_name}...")
api = SpheroEduAPI(toy)
print(f"Connected to {toy_name} ✅")

# LED Green means ready
api.set_front_led(Color(0, 255, 0))

# ----------------------------
# Helper Functions
# ----------------------------
def draw_text(text, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def get_battery_level():
    try:
        voltage = Power.get_battery_voltage(toy)
        return voltage
    except Exception as e:
        print(f"Battery check failed: {e}")
        return None

def set_speed_color(speed):
    """Change LED color based on speed tier."""
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

# ----------------------------
# Main Loop
# ----------------------------
try:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                api.set_speed(0)
                pygame.quit()
                sys.exit()

        screen.fill((20, 20, 20))

        # Joystick axes
        x_axis = joystick.get_axis(0)
        y_axis = joystick.get_axis(1)

        # Shoulder buttons for calibration (offset rotation)
        if joystick.get_button(4):  # L1
            angle_offset += 2
        if joystick.get_button(5):  # R1
            angle_offset -= 2
        angle_offset %= 360

        # Speed tier buttons
        if joystick.get_button(0):
            speed = 50
            set_speed_color(speed)
        if joystick.get_button(1):
            speed = 70
            set_speed_color(speed)
        if joystick.get_button(2):
            speed = 100
            set_speed_color(speed)
        if joystick.get_button(3):
            speed = 200
            set_speed_color(speed)

        # Joystick strength
        strength = math.sqrt(x_axis ** 2 + y_axis ** 2)
        if strength < DEADZONE:
            strength = 0

        # Compute heading
        if strength > 0:
            angle = math.degrees(math.atan2(-y_axis, x_axis)) - 90 + angle_offset
            angle %= 360
            api.set_heading(angle)
            api.set_speed(speed)
        else:
            api.set_speed(0)

        # Draw UI
        draw_text(f"Joystick: ({x_axis:.2f}, {y_axis:.2f})", (255, 255, 255), 10, 10)
        draw_text(f"Angle: {angle:.2f}", (255, 255, 255), 10, 35)
        draw_text(f"Angle Offset: {angle_offset:.2f}", (255, 255, 255), 10, 60)
        draw_text(f"Speed: {speed}", (255, 255, 0), 10, 85)

        rotated_arrow = pygame.transform.rotate(arrow_image, angle)
        rect = rotated_arrow.get_rect(center=arrow_location)
        screen.blit(rotated_arrow, rect.topleft)

        # Check battery every BATTERY_CHECK_INTERVAL seconds
        if time.time() - last_battery_time >= BATTERY_CHECK_INTERVAL:
            voltage = get_battery_level()
            if voltage:
                print(f"Battery voltage: {voltage:.2f} V")
            last_battery_time = time.time()

        pygame.display.flip()
        clock.tick(FPS)

finally:
    api.set_speed(0)
    pygame.quit()