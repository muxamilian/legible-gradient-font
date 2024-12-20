from PIL import Image, ImageFont, ImageDraw
import string
import torchvision.transforms as T
import os
import numpy as np

out_dir = 'out' 
os.makedirs(out_dir, exist_ok=True)

# Constants
# FONT_PATH = "RobotoMono-VariableFont_wght.ttf"
FONT_PATH = "Roboto-Regular.ttf"
IMG_SIZE = (224, 224)
ASCII_PRINTABLE = string.printable  # All printable ASCII characters

def generate_char_images(font_path, img_size=(224, 224)):
    space_width = None
    """Generate 64x64 matrices for each printable ASCII character."""
    # Specify font size in pixels and the image's DPI
    font_size = 160
    font = ImageFont.truetype(font_path, size=font_size)  # Adjust size to fit in 64x64
    char_images = []
    sizes = []
    text_sizes = []
    positions = []
    actual_ascii = ''

    for char in ASCII_PRINTABLE:
        if len(char.strip()) == 0 and char != ' ':
            continue
        # Create a blank image and a drawing context
        image = Image.new('L', img_size, color=255)  # 'L' mode for grayscale
        draw = ImageDraw.Draw(image)
        
        # Get character size and calculate positioning
        text_left, text_top, text_right, text_bottom = draw.textbbox((0,0), char, font=font, font_size=font_size, spacing=0) 
        text_size = (text_right - text_left, text_bottom - text_top)
        if char == ' ':
            space_width = text_size[0]
            continue
        actual_ascii += char
        sizes.append([text_left, text_top, text_right, text_bottom])
        text_sizes.append(text_size)
        position = ((img_size[0] - text_size[0]) // 2, 0)
        positions.append(position)
        
        # Draw character onto the image
        draw.text(position, char, fill=0, font=font)
        char_for_filename = char.replace('.', 'dot').replace('/', 'slash').replace(':', 'colon')
        image.save(f'{out_dir}/{char_for_filename}.png')

        # Convert image to numpy array and normalize
        char_images.append(np.array(image) / 255.0)
    
    return char_images, sizes, text_sizes, positions, actual_ascii, space_width


def save_img(batch, name):
    
    n_columns = 10
    n_images = len(batch)
    n_rows = (n_images + n_columns - 1) // n_columns  # Calculate required rows

    # Define a transform to convert the tensor to a PIL image
    to_pil = T.ToPILImage()

    # Image size (assuming all images are the same size)
    img_width, img_height = 224, 224

    def extend(img_pil):
        nonlocal img_width, img_height
        # Get the dimensions of the image
        width, height = img_pil.size

        # Check if the size is already 224x224
        if width == img_width and height == img_height:
            return img_pil  # No changes needed

        # Create a new image with a black (or any color) background
        new_img = Image.new("RGB", (224, 224), (0, 0, 0))  # Black background

        # Calculate the position to center the original image
        left = (img_width - width) // 2
        top = (img_height - height) // 2

        # Paste the original image onto the new image
        new_img.paste(img_pil, (left, top))

        return new_img

    # Create a blank canvas for the tiled image
    tiled_image = Image.new('RGB', (n_columns * img_width, n_rows * img_height))

    # Loop over each image and paste it on the canvas
    for i in range(n_images):
        img_tensor = batch[i]
        
        img_pil = extend(to_pil(img_tensor))  # Convert to PIL Image
        
        # Calculate position in the grid
        row = i // n_columns
        col = i % n_columns
        
        # Paste the image in the correct position
        tiled_image.paste(img_pil, (col * img_width, row * img_height))
    tiled_image.save(f'{name}.png')


def parse_tiled_image(image_path, img_size=(224, 224), n_columns=10):
    """
    Parse a tiled image and extract individual character images.
    
    Args:
        image_path (str): Path to the PNG image generated by save_img.
        img_size (tuple): Size of each character image (width, height).
        n_columns (int): Number of columns in the grid.

    Returns:
        List of numpy arrays, each representing an individual character image.
    """
    # Open the tiled image
    tiled_image = Image.open(image_path)
    img_width, img_height = img_size
    
    # Calculate the number of images in the grid based on image height
    n_rows = tiled_image.height // img_height

    # List to hold extracted character images
    char_images = []

    # Loop over each cell in the grid
    for row in range(n_rows):
        for col in range(n_columns):                
            # Define the bounding box for each cell
            left = col * img_width
            upper = row * img_height
            right = left + img_width
            lower = upper + img_height

            # Crop the character image and convert to numpy array
            char_image = tiled_image.crop((left, upper, right, lower))
            normalized = np.array(char_image) / 255.0

            if np.all(normalized == 0.0):
                return char_images
            char_images.append(normalized)  # Normalize to [0, 1]
