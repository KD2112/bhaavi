import os
import sys
import json
import cv2
import requests
import image_to_base64
from PIL import Image, ImageDraw, ImageFont

def get_data(json_data, url):
    """
    Sends JSON data to the FastAPI application and returns the response.

    :param json_data: The JSON data to send.
    :param url: The URL of the FastAPI application's endpoint.
    :return: Parsed JSON response or None if the request failed.
    """
    try:
        response = requests.post(url, json=json_data)
        
        # Check if the request was successful
        if response.status_code == 200:
            return response.json()  # Return parsed JSON response
        else:
            print(f"Failed to send image. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while sending the request: {e}")
        return None

def run(input_json, image_path):
    server_url = 'http://192.168.134.248:8001/anpr'
    
    print("Processing data...")
    output = get_data(json_data=input_json, url=server_url)
    
    if output is not None:
        print("\nOutput from the application:")
        print(json.dumps(output, indent=4))  # Pretty print the output
    else:
        print("No output received.")
        return
    
    # Open the image using Pillow
    image = Image.open(image_path)
    
    # Add the license plate number to the image
    license_plate_number = output["result"]["license_plate_number"]
    vehicle_image_with_text = add_license_plate_to_image(image, license_plate_number)

    # Save the e_path = os.path.join('/home/trois/Neenu/image', f"vehicle_with_{license_plate_number}.jpg")
    vehicle_image_with_text.save(output_image_path)
    print(f"Saved image with license plate text at: {output_image_path}")

def get_json(image_bright, image_dark, image_height, image_width):
    """
    Constructs the JSON payload to be sent to the FastAPI application.

    :param image_bright: Base64 encoded bright image.
    :param image_dark: Base64 encoded dark image.
    :param image_height: Height of the image.
    :param image_width: Width of the image.
    :return: A dictionary representing the JSON payload.
    """
    return {
        "object-id": 1,
        "vehicle-id": 2,
        "image_bright": image_bright,
        "image_dark": image_dark,
        "bbox": [0, 0, image_width, image_height],
        "lpd": True,
        "lpr": True
    }

def process_images(input_folder):
    """
    Processes all images in the specified folder and sends them to the FastAPI application.

    :param input_folder: Path to the folder containing images.
    """
    for image_name in os.listdir(input_folder):
        image_path = os.path.join(input_folder, image_name)
        
        # Read and process the image
        cv2_image = cv2.imread(image_path)
        if cv2_image is None:
            print(f"Could not read image: {image_path}. Skipping.")
            continue

        height, width, _ = cv2_image.shape
        image_bright = image_to_base64.image_to_base64(image_path)
        image_dark = image_to_base64.image_to_base64(image_path)

        input_json = get_json(image_bright=image_bright, image_dark=image_dark,
                               image_height=height, image_width=width)
        
        run(input_json=input_json, image_path=image_path)


# Function to add text to the image
def add_license_plate_to_image(image, license_plate_number):
    """
    Adds the license plate number text to the top-left corner of the image with a larger font size.

    :param image: PIL.Image object of the image.
    :param license_plate_number: The text to add to the image.
    :return: Modified PIL.Image object.
    """
    # Prepare drawing context
    draw = ImageDraw.Draw(image)
    
    # Use a custom font and specify the font size
    font_size = 30  # Increase the font size as needed
    try:
        font = ImageFont.truetype("arial.ttf", font_size)  # Use Arial or any installed font
    except IOError:
        print("Custom font not found. Falling back to default font.")
        font = ImageFont.load_default()  # Fallback to default if Arial is not found

    # Define text position and color
    text_position = (10, 10)  # Position at the top-left corner
    text_color = (255, 255, 255)  # White text color

    # Add the license plate number text
    draw.text(text_position, license_plate_number, fill=text_color, font=font)
    return image
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 image_folder_client.py <image_folder>")
        sys.exit(1)  # Exit with an error code
    
    input_folder = sys.argv[1]
    output_image_path=sys.argv[2]

    if not os.path.isdir(input_folder):
        print(f"The specified path is not a directory: {input_folder}")
        sys.exit(1)  # Exit with an error code
    
    process_images(input_folder)

if __name__ == '__main__':
    main()
