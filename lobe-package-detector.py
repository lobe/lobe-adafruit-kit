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
import adafruit_dotstar
from datetime import datetime

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

DOTSTAR_DATA = board.D5
DOTSTAR_CLOCK = board.D6

RED = (0, 0, 255)
GREEN = (255, 0, 0)
OFF = (0, 0, 0)

dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)

def color_fill(color, wait):
    dots.fill(color)
    dots.show()
    time.sleep(wait)


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
		label = ''
		last_label = ''
		while True:
			stream.seek(0)
			camera.annotate_text = None
			camera.capture(stream, format='jpeg')
			camera.annotate_text = label
			img = Image.open(stream)
			result = model.predict(img)
			label = result.prediction
			confidence = result.labels[0][1]
			camera.annotate_text = label
			print(f'\rLabel: {label} | Confidence: {confidence*100: .2f}%', end='', flush=True)

			# Check if the current label is package and that the label has changed since last tine the code ran
			if (label == 'package' and last_label != 'package'):
				
				# Send an HTTP POST request to the IFTTT using the label and key
				response = requests.post(f'https://maker.ifttt.com/trigger/{label}/with/key/{key}')

				# Set the last label to package, so IFTTT is only triggered once per package
				last_label = 'package'

				if (response.status_code == 401):
					print(f'IFTTT Error: Your API key is invalid or has not been configured yet')
				continue

			last_label = label

			inputs = get_inputs()
			# Check if the joystick is pushed up
			if (Input.UP in inputs):
				color_fill(GREEN, 0)
				# If there isn't one already ceate a folder in the retraining folder for the current label
				if (not os.path.exists(f'./retraining_data/{label}')):
					os.mkdir(f'./retraining_data/{label}')
				# Remove the text annodtation
				camera.annotate_text = None

				# File name
				name = datetime.now()
				# Save the current frame
				camera.capture(
					os.path.join(
						f'./retraining_data/{label}', 
						f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}.jpg'
					)
				)
				
				color_fill(OFF, 0)

			# Check if the joystick is pushed down
			elif (Input.DOWN in inputs or Input.BUTTON in inputs):
				color_fill(RED, 0)
				# Remove the text annodtation
				camera.annotate_text = None
				# Save the current frame to the top level retraining directory
				camera.capture(
					os.path.join(
						f'./retraining_data',
						f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}.jpg'
					)
				)
				color_fill(OFF, 0)


if __name__ == '__main__':
	try:
		print(f"Predictions starting, to stop press \"CTRL+C\"")
		main()
	except KeyboardInterrupt:
		print("")
		print(f"Caught interrupt, exiting...")
