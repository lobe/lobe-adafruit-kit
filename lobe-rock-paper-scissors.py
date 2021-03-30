import time
import board
import picamera
import io
import random
from PIL import Image
from lobe import ImageModel
from enum import Enum, auto
from digitalio import DigitalInOut, Direction, Pull

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

# The 3 signs that a player may play
signs = ['Rock', 'Paper', 'Scissors']

# Define the game logic in a dictionary.
# The string on the left beats the string on the right.
game_logic = {'Rock' : 'Paper',
			  'Paper' : 'Scissors',
			  'Scissors' : 'Rock'}

def load_image(path, camera) -> Image:
	img = Image.open(path)

	pad = Image.new('RGB', (
		((img.size[0] + 31) // 32) * 32,
		((img.size[1] + 15) // 16) * 16,
		))

	pad.paste(img, (0, 0))
	
	layer = camera.add_overlay(pad.tobytes(), size=img.size)

	return layer

# Choose an element of the "signs" list at random
def random_sign():
	return random.choice(signs)

def compare_signs(player_sign, computer_sign):
	if (game_logic[player_sign] == computer_sign):
		return 'computer'
	elif (game_logic[computer_sign] == player_sign):
		return 'player'
	else:
		return 'tie'


def main():
	model = ImageModel.load('~/model')

	with picamera.PiCamera(resolution=(224, 224), framerate=30) as camera:

		# Start showing camera on screen
		stream = io.BytesIO()
		camera.start_preview()
		# Camera warm-up time
		time.sleep(2)
		
		# Load all the images for the game
		rock = load_image('rock.png', camera)
		paper = load_image('paper.png', camera)
		scissors = load_image('scissors.png', camera)
		counter_one = load_image('one.png', camera)
		counter_two = load_image('two.png', camera)
		counter_three = load_image('three.png', camera)


		# Loop this section forever
		while True:
			stream.seek(0)

			# Wait for the button to be pressed for the game to start
			inputs = get_inputs()
			while Input.BUTTON not in inputs:
				inputs = get_inputs()
				time.sleep(0.1)
			
			# Clear annocated text
			camera.annotate_text = ''

			# Turn the opacity of the camera to 0
			camera.preview.alpha = 0
			
			# Move the counter_one layer to the top
			counter_three.layer = 3
			time.sleep(1)
			counter_three.layer = 0
			counter_two.layer = 3
			time.sleep(1)
			counter_two.layer = 0
			counter_one.layer = 3
			time.sleep(1)
			counter_one.layer = 0
			camera.preview.alpha = 255
			time.sleep(1)

			# Capture a single image
			camera.capture(stream, format='jpeg')
			img = Image.open(stream)

			# Run inference on the image
			result = model.predict(img)

			# Get the label predicted by the model
			label = result.prediction

			# Show label over the camera preview
			camera.annotate_text = label
			time.sleep(2)

			computer_sign = random_sign()
			
			if (computer_sign == 'Rock'):
				rock.layer = 3
			elif (computer_sign == 'Paper'):
				paper.layer = 3
			elif (computer_sign == 'Scissors'):
				scissors.layer = 3

			time.sleep(2)

			# Hide all the layers with the images of the computer signs
			rock.layer = 0
			paper.layer = 0
			scissors.layer = 0
			
			winner = compare_signs(label, computer_sign)

			if (winner == 'player'):
				camera.annotate_text = 'You Win!'
			elif (winner == 'computer'):
				camera.annotate_text = 'You Lose...'
			elif (winner == 'tie'):
				camera.annotate_text = 'Tie'


if __name__ == '__main__':
	try:
		print(f"Predictions starting, to stop press \"CTRL+C\"")
		main()
	except KeyboardInterrupt:
		print("")
		print(f"Caught interrupt, exiting...")
