import time
from enum import Enum, auto
import board
from digitalio import DigitalInOut, Direction, Pull
import picamera
import io
from PIL import Image
from lobe import ImageModel
import os
import requests

# Boiler Plate code for buttons and joystick on the braincraft
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

# Load the IFTTTT key from the environment variable on the Pi
key = os.getenv('IFTTTKEY')

def main():
	model = ImageModel.load('~/model')

	# Check if there is a folder to keep the retraining data, if it there isn't make it
	if (not os.path.exists('./retraining_data')):
		os.mkdir('./retraining_data')

	with picamera.PiCamera(resolution=(224, 224), framerate=30) as camera:
		stream = io.BytesIO()
		camera.start_preview()
		# Camera warm-up time
		time.sleep(2)
		i = 0
		while True:
			stream.seek(0)
			camera.capture(stream, format='jpeg')
			img = Image.open(stream)
			result = model.predict(img)
			label = result.prediction
			camera.annotate_text = label
			print(f'\r{label}', end='', flush=True)

			# Check if the current label is package and that the label has changed since last tine the code ran
			if (label == 'package' and last_label != 'package'):
				# Send an HTTP POST request to the IFTTT using the label and key
				repsonse = requests.post(f'https://maker.ifttt.com/trigger/{label}/with/key/{key}')
				print(repsonse.content.decode('utf-8'))
				# Set the last label to package, so IFTTT is only triggered once per package
				last_label = 'package'
				continue

			last_label = label

			inputs = get_inputs()

			# Check if the joystick is pushed up
			if (Input.UP in inputs):
				# If there isn't one already ceate a folder in the retraining folder for the current label
				if (not os.path.exists(f'./retraining_data/{label}')):
					os.mkdir(f'./retraining_data/{label}')
				# Remove the text annodtation
				camera.annotate_text = None
				# Save the current frame
				camera.capture(os.path.join(f'./retraining_data/{label}', f'{i}.jpg'))
				i += 1

			# Check if the joystick is pushed down
			elif (Input.DOWN in inputs or Input.BUTTON in inputs):
				# Remove the text annodtation
				camera.annotate_text = None
				# Save the current frame to the top level retraining directory
				camera.capture(os.path.join(f'./retraining_data', f"{i}.jpg"))
				i += 1


if __name__ == '__main__':
	try:
		print(f"Predictions starting, to stop press \"CTRL+C\"")
		main()
	except KeyboardInterrupt:
		print("")
		print(f"Caught interrupt, exiting...")
