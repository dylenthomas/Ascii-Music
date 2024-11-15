import io 
import numpy as np
import PIL
from PIL import Image 

def convert_image_to_ascii(image_data:bytes, new_width=None, rescale_ratio=None, is_negative=False, in_image_size:tuple=None) -> str:
    ascii = [" ", "`", ".", ",", ":", "*", "~", "r", "c", "o", "a", "/", "?", "%", ")", "}", "l", "L", "I", "K", "T", "A", "S", "O", "@", "M"]
    if is_negative:
        ascii = ascii[::-1]
    try:
        image = Image.open(io.BytesIO(image_data))
    except PIL.UnidentifiedImageError:
        image = Image.frombytes('RGB', in_image_size, image_data)

    image = image.convert('RGB')
    image = np.array(image)
    
    # Gray scale using weighted average
    weights = np.array([0.299, 0.587, 0.114])
    image = np.dot(image[..., :3], weights).astype(np.uint8)

    if new_width is None:
        new_width = image.shape[1]
    
    if rescale_ratio is None:
        rescale_ratio = image.shape[0] / image.shape[1]

    image = Image.fromarray(image)

    height, width = image.size
    ratio = height / width * rescale_ratio
    new_height = int(new_width * ratio)
    image = image.resize((new_width, new_height)) #resize image to make the ascii image smaller 
    
    pixels = image.getdata()
    ascii_chars = ''.join(ascii[pixel//10] for pixel in pixels)
    num_char = len(ascii_chars)

    image = '\n'.join(ascii_chars[index:(index + new_width)] for index in range(0, num_char, new_width))
    
    return image
