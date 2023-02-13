from tqdm import tqdm
import os
import random
import subprocess
from PIL import Image

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("background_path", type=str,
                    help="path to folder with background images")
parser.add_argument("foreground_path", type=str,
                    help="path to folder with foreground images")
parser.add_argument("output_path", type=str,
                    help="path to output with composites and labels")

parser.add_argument("--quantity", type=int, default=10,
                    help="number of composites to generate")
parser.add_argument("--prefix", type=str, default="img",
                    help="filename prefix for output images and labels")

parser.add_argument("--size", type=int, default=640,
                    help="target image size (px)")

parser.add_argument("--enable-resize", type=bool, default=True,
                    help="enable random image resizing")
parser.add_argument("--resize-min", type=float, default=0.5,
                    help="minimum random img size")
parser.add_argument("--resize-max", type=float, default=1.5,
                    help="maximum random img size")

parser.add_argument("--magick", type=str, default="magick",
                    help="set imagemagick executable")
args = parser.parse_args()


# Number of images to generate
total_image_number = args.quantity

# Paths to the folders
backgrounds_path = args.background_path
foregrounds_path = args.foreground_path

output_path = args.output_path
output_file_prefix = args.prefix

images_suffix = "images"
labels_suffix = "labels"

fg_random_resize_enabled = args.enable_resize
fg_random_resize_max = args.resize_max if fg_random_resize_enabled else 1
fg_random_resize_min = args.resize_min if fg_random_resize_enabled else 1

output_size = args.size

magick = args.magick


# Get the list of background and foreground images
backgrounds = os.listdir(backgrounds_path)
foregrounds = os.listdir(foregrounds_path)

# Function to get image size

def get_image_size(image_path):
    with Image.open(image_path) as img:
        return img.size

# Get size of each background image
backgrounds_with_sizes = [
    (
        os.path.join(backgrounds_path, bg),
        get_image_size(os.path.join(backgrounds_path, bg))
    )
    for bg in backgrounds
]
foregrounds_with_sizes = [
    (
        os.path.join(foregrounds_path, fg),
        get_image_size(os.path.join(foregrounds_path, fg))
    )
    for fg in foregrounds
]

output_image_folder = os.path.join(
    output_path, images_suffix)
output_label_folder = os.path.join(
    output_path, labels_suffix)

if not os.path.exists(output_path):
    os.mkdir(output_path)

if not os.path.exists(output_image_folder):
    os.mkdir(output_image_folder)

if not os.path.exists(output_label_folder):
    os.mkdir(output_label_folder)

# Use tqdm for progress bar
for i in tqdm(range(total_image_number)):
    # Pick a random background and foreground
    (background_fullpath, bg_size) = random.choice(backgrounds_with_sizes)
    (foreground_fullpath, fg_size) = random.choice(foregrounds_with_sizes)

    # Generate random x and y coordinates for the composite
    (fg_width, fg_height) = fg_size
    (bg_width, bg_height) = bg_size

    max_fg_scalefactor = min(bg_width/fg_width, bg_height/fg_height)
    fg_scalefactor = random.uniform(fg_random_resize_min, min(
        max_fg_scalefactor, fg_random_resize_max))

    fg_width = int(fg_width * fg_scalefactor)
    fg_height = int(fg_height * fg_scalefactor)

    x_offset = random.randint(0, bg_width - fg_width)
    y_offset = random.randint(0, bg_height - fg_height)

    output_image_filename = f"{output_file_prefix}_{i}.png"
    output_label_filename = f"{output_file_prefix}_{i}.txt"

    output_image_fullpath = os.path.join(
        output_image_folder, output_image_filename)
    output_label_fullpath = os.path.join(
        output_label_folder, output_label_filename)

    # Generate the composite
    command = f"{magick} convert \"{background_fullpath}\" \"{foreground_fullpath}\" -geometry {fg_width}x{fg_height}+{x_offset}+{y_offset} -composite -resize {output_size}x{output_size} \"{output_image_fullpath}\""
    subprocess.run(command, shell=True, capture_output=True, check=True)

    # # # Resize the composite and add black bars if necessary
    # output_size_magick = f"{output_size}x{output_size}"
    # command = f"{magick} convert {output_image_fullpath} -resize {output_size_magick}^ -background black -gravity center -extent {output_size_magick} {output_image_fullpath}"
    # subprocess.run(command, shell=True, capture_output=True, check=True)

    # Generate the label
    # # assume image output is a square, and image is wider than tall, compute the vertical black bar
    # vertical_black_bar_height = bg_width

    # normalize coordinates

    x_center = int(x_offset + fg_width/2)
    y_center = int(y_offset + fg_height/2)

    label_output_text = f"0 {x_center/bg_width} {y_center/bg_height} {fg_width/bg_width} {fg_height/bg_height}"

    with open(output_label_fullpath, "w") as f:
        f.write(label_output_text)
