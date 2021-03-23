import time
from enum import Enum, auto
import board
from digitalio import DigitalInOut, Direction, Pull
import picamera
import io
from PIL import Image

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


def main():
	with picamera.PiCamera(resolution=(224, 224), framerate=30) as camera:
		stream = io.BytesIO()
		camera.start_preview()
		# Camera warm-up time
		time.sleep(2)
		i = 0
		while True:
			stream.seek(0)
			inputs = get_inputs()
			camera.capture(stream, format='jpeg')
			img = Image.open(stream)
			if Input.UP in inputs:
				img.save(f"{i}.jpg")
				i += 1


if __name__ == '__main__':
	try:
		print(f"Capture starting, to stop press \"CTRL+C\"")
		main()
	except KeyboardInterrupt:
		print("")
		print(f"Caught interrupt, exiting...")
