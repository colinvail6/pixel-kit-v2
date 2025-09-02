"""
PixelKit v2.0 for CircuitPython
- Reads pause pin+direction from pausebutton_pin_config.txt
"""

import sys
import board
import digitalio
import analogio
import neopixel
from adafruit_pixel_framebuf import PixelFramebuffer


class PixelKit:
    # Class-level pin registries
    _dio_registry = {}
    _ain_registry = {}

    def __init__(
        self,
        pause=None,
        button_A=None,
        button_B=None,
        button_reset=None,
        joystick_up=None,
        joystick_down=None,
        joystick_left=None,
        joystick_right=None,
        joystick_click=None,
        dial=None,
        microphone=None,
        pause_config_file="pausebutton_pin_config.txt"
    ):
        # --- NeoPixels ---
        self.neopixel_instance = neopixel.NeoPixel(board.D4, 128, auto_write=False)
        self.matrix_instance = PixelFramebuffer(self.neopixel_instance, 16, 8)

        # --- Pause Button ---
        self.pause = pause if pause is not None else self._load_pause_from_file(pause_config_file)

        # --- Digital Pins ---
        self.button_A = self._init_dio(button_A, board.D18)
        self.button_B = self._init_dio(button_B, board.D23)
        self.button_reset = self._init_dio(button_reset, board.D5)
        self.joystick_up = self._init_dio(joystick_up, board.D35)
        self.joystick_down = self._init_dio(joystick_down, board.D34)
        self.joystick_left = self._init_dio(joystick_left, board.D26)
        self.joystick_right = self._init_dio(joystick_right, board.D25)
        self.joystick_click = self._init_dio(joystick_click, board.D27)

        # --- Analog Pins ---
        self.dial = self._init_ain(dial, board.VP)
        self.microphone = self._init_ain(microphone, board.VN)

        # --- State ---
        self.dial_value = self.dial.value
        self.microphone_value = self.microphone.value
        self.is_pressing_up = False
        self.is_pressing_down = False
        self.is_pressing_left = False
        self.is_pressing_right = False
        self.is_pressing_click = False
        self.is_pressing_a = False
        self.is_pressing_b = False

    # -------- Pin helpers with registry --------
    def _init_dio(self, instance, board_pin):
        """Return existing DigitalInOut or create new one safely."""
        if instance is not None:
            return instance
        if board_pin in PixelKit._dio_registry:
            return PixelKit._dio_registry[board_pin]
        dio = digitalio.DigitalInOut(board_pin)
        dio.direction = digitalio.Direction.INPUT
        dio.pull = digitalio.Pull.UP
        PixelKit._dio_registry[board_pin] = dio
        return dio

    def _init_ain(self, instance, board_pin):
        """Return existing AnalogIn or create new one safely."""
        if instance is not None:
            return instance
        if board_pin in PixelKit._ain_registry:
            return PixelKit._ain_registry[board_pin]
        ain = analogio.AnalogIn(board_pin)
        PixelKit._ain_registry[board_pin] = ain
        return ain

    # -------- Pause config helper --------
    def _load_pause_from_file(self, filename):
        """
        Reads '<PIN_NAME>,<DIR>' from root file, e.g. 'D15,IN'.
        Returns a configured DigitalInOut or None if file missing/invalid.
        """
        try:
            with open(filename, "r") as f:
                line = f.readline().strip()
            if not line:
                print("Pause config empty -> no pause button")
                return None

            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 2:
                print("Pause config malformed -> no pause button")
                return None

            pin_name, direction = parts[0], parts[1].upper()
            try:
                pin_obj = getattr(board, pin_name)
            except AttributeError:
                print("Pause config pin not found on this board:", pin_name)
                return None

            # Reuse existing DigitalInOut if available
            dio = self._init_dio(None, pin_obj)
            if direction == "IN":
                dio.direction = digitalio.Direction.INPUT
                dio.pull = digitalio.Pull.UP
            elif direction == "OUT":
                dio.direction = digitalio.Direction.OUTPUT
            else:
                print("Pause config invalid direction:", direction)
                return None

            print("Pause button from config:", pin_name, direction)
            return dio

        except OSError:
            return None
        except Exception as e:
            print("Pause config error:", e)
            return None

    # -------- Input scanning --------
    def check_controls(self):
        self._check_joystick()
        self._check_buttons()
        self._check_dial()
        self._check_microphone()
        self._update_pause()

    def _check_joystick(self):
        self._check_digital(self.joystick_up, "up", is_joystick=True)
        self._check_digital(self.joystick_down, "down", is_joystick=True)
        self._check_digital(self.joystick_left, "left", is_joystick=True)
        self._check_digital(self.joystick_right, "right", is_joystick=True)
        self._check_digital(self.joystick_click, "click", is_joystick=True)

    def _check_buttons(self):
        self._check_digital(self.button_A, "a")
        self._check_digital(self.button_B, "b")

    def _check_digital(self, dio, name, is_joystick=False):
        state_attr = f"is_pressing_{name}"
        event_method = getattr(self, f"on_{'joystick_' if is_joystick else 'button_'}{name}")
        pressing = getattr(self, state_attr)
        if not dio.value and not pressing:
            setattr(self, state_attr, True)
            event_method()
        elif dio.value and pressing:
            setattr(self, state_attr, False)

    def _check_dial(self):
        new_value = self.dial.value
        if new_value != self.dial_value:
            self.dial_value = new_value
            self.on_dial(new_value)

    def _check_microphone(self):
        new_value = self.microphone.value
        if new_value != self.microphone_value:
            self.microphone_value = new_value
            self.on_microphone(new_value)

    # -------- Pause behavior --------
    def _update_pause(self):
        if self.pause and not self.pause.value:  # active-low
            self.neopixel_instance.fill((0, 0, 0))
            self.neopixel_instance.show()
            print("Pause pressed -> exiting")
            sys.exit()

    # -------- Event hooks (override) --------
    def on_joystick_up(self): return False
    def on_joystick_down(self): return False
    def on_joystick_left(self): return False
    def on_joystick_right(self): return False
    def on_joystick_click(self): return False
    def on_button_a(self): return False
    def on_button_b(self): return False
    def on_dial(self, value): return False
    def on_microphone(self, value): return False

    # -------- LED helpers --------
    def set_pixel(self, x, y, color=0x00FF00):
        self.matrix_instance.pixel(x, y, color)

    def set_background(self, color=0x00FF00):
        self.matrix_instance.fill(color)

    def clear(self):
        self.set_background(0x000000)

    def render(self):
        self.matrix_instance.display()
