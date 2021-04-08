import time
import picamera
import io
from PIL import Image
from lobe import ImageModel

def main():
	# Load Lobe model
	model = ImageModel.load('~/model')
	with picamera.PiCamera(resolution=(224, 224), framerate=30) as camera:
		
		# Start camera preview
		stream = io.BytesIO()
		camera.start_preview()

		# Camera warm-up time
		time.sleep(2)

		while True:
			# Start stream at the first byte
			stream.seek(0)

			# Start performance counter
			start = time.perf_counter()

			# Clear the last prediction text
			camera.annotate_text = None

			# Capture a single frame as a Pillow image
			camera.capture(stream, format='jpeg')
			img = Image.open(stream)

			# Start prediction performance timer
			predict_start = time.perf_counter()

			# Run inference on the image
			result = model.predict(img)

			# End prediction performance timer
			predict_end = time.perf_counter()

			# Get the prediction label
			label = result.prediction

			# Get the confidence for the top label
			confidence = result.labels[0][1]

			# Add label text to camera preview
			camera.annotate_text = label

			# End performance timer
			end = time.perf_counter()

			# Calculate prediction time
			predict_time = predict_end - predict_start

			# Calculate program run time
			total_time = end - start

			# Print performance times
			print(f"\rLabel: {label} | Confidence: {confidence*100: .2f}% | FPS: {1/total_time: .2f} | prediction fps: {1/predict_time: .2f} | {predict_time/total_time: .2f}", end='', flush=True)

			# Wait for 1 second so the label is visible on the screen
			time.sleep(1)


if __name__ == '__main__':
	try:
		print(f"Predictions starting, to stop press \"CTRL+C\"")
		main()
	except KeyboardInterrupt:
		print("")
		print(f"Caught interrupt, exiting...")