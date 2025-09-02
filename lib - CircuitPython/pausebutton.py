# pausebutton.py
import sys, time, board, digitalio

class PauseButton:
    def __init__(self, button=None, leds=None, config_file=None):
        self.leds = leds
        self.paused = False

        if config_file:
            self.button = self._load_from_file(config_file)
        else:
            self.button = button

    def _load_from_file(self, filename, default_pin="IO15", default_dir="IN"):
        try:
            with open(filename) as f:
                line = f.readline().strip()
                if not line:
                    raise ValueError("Empty config file")
                pin_name, direction = [x.strip() for x in line.split(",")]
        except Exception as e:
            print("PauseButton config error:", e, "-> using defaults")
            pin_name, direction = default_pin, default_dir

        # resolve pin object from board
        pin = getattr(board, pin_name)

        # create DigitalInOut
        dio = digitalio.DigitalInOut(pin)

        # apply direction
        if direction.upper() == "IN":
            dio.direction = digitalio.Direction.INPUT
            dio.pull = digitalio.Pull.UP
        elif direction.upper() == "OUT":
            dio.direction = digitalio.Direction.OUTPUT
        else:
            raise ValueError("Invalid direction in config")

        return dio

    def update(self):
        """Call this once per loop to check the button."""
        if self.button and not self.button.value:
            if self.leds:
                self.leds.fill((0,0,0))
            print("PauseButton pressed! Exiting...")
            sys.exit()
