import time
from enum import Enum, auto
import board
from digitalio import DigitalInOut, Direction, Pull
import picamera
import io
from PIL import Image
from datetime import datetime
import adafruit_dotstar

BUTTON_PIN = board.D17
JOYDOWN_PIN = board.D27
JOYLEFT_PIN = board.D22
JOYUP_PIN = board.D23
JOYRIGHT_PIN = board.D24
JOYSELECT_PIN = board.D16

buttons = [BUTTON_PIN, JOYUP_PIN, JOYDOWN_PIN,
           JOYLEFT_PIN, JOYRIGHT_PIN, JOYSELECT_PIN]

for i, pin in enumerate(buttons):
	buttons[i] = DigitalInOut(pin)
	buttons[i].direction = Direction.INPUT
	buttons[i].pull = Pull.UP
button, joyup, joydown, joyleft, joyright, joyselect = buttons


class Input(Enum):
	BUTTON = auto()
	UP = auto()
	DOWN = auto()
	LEFT = auto()
	RIGHT = auto()
	SELECT = auto()


def get_inputs():
	inputs = []
	if not button.value:
		inputs.append(Input.BUTTON)
	if not joyup.value:
		inputs.append(Input.UP)
	if not joydown.value:
		inputs.append(Input.DOWN)
	if not joyleft.value:
		inputs.append(Input.LEFT)
	if not joyright.value:
		inputs.append(Input.RIGHT)
	if not joyselect.value:
		inputs.append(Input.SELECT)
	return inputs

DOTSTAR_DATA = board.D5
DOTSTAR_CLOCK = board.D6

GREEN = (255, 0, 0)
OFF = (0, 0, 0)

dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.1)

def color_fill(color, wait):
    dots.fill(color)
    dots.show()
    time.sleep(wait)

def main():
	with picamera.PiCamera(resolution=(224, 224), framerate=30) as camera:
		stream = io.BytesIO()
		camera.start_preview()
		# Camera warm-up time
		time.sleep(2)

		while True:
			camera.annotate_text = "Ready..."
			stream.seek(0)
			inputs = get_inputs()

			if Input.BUTTON in inputs:
				color_fill(GREEN, 0)
				camera.annotate_text = None
				camera.capture(stream, format='jpeg')
				img = Image.open(stream)
				img.save(f"{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}.jpg")
			
			color_fill(OFF, 0)
			time.sleep(0.1)



if __name__ == '__main__':
	try:
		print(f"Capture starting, to stop press \"CTRL+C\"")
		main()
	except KeyboardInterrupt:
		print("")
		print(f"Caught interrupt, exiting...")
