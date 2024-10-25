#!/usr/bin/env python3

from PIL import Image
import moviepy.editor as mpy
import numpy as np


def ken_burns_effect(
    image_path, output_video_path, duration=4, zoom_factor=1.2, fps=30
):
    # Open the image
    img = Image.open(image_path)
    img_width, img_height = img.size

    # Create a list to store frames
    frames = []

    # Number of frames for the duration of the video
    total_frames = duration * fps

    # Define start and end zoom levels (center crop and zoom)
    start_scale = 1.0  # Start with no zoom
    end_scale = zoom_factor  # Zoom in by the given factor

    # Loop through each frame
    for i in range(total_frames):
        # Calculate interpolation scale for the current frame
        scale = start_scale + (end_scale - start_scale) * (i / total_frames)

        # Calculate new dimensions for the current frame
        new_width = int(img_width / scale)
        new_height = int(img_height / scale)

        # Center crop coordinates
        left = (img_width - new_width) // 2
        top = (img_height - new_height) // 2
        right = left + new_width
        bottom = top + new_height

        # Crop and resize the image back to the original size (simulate zoom)
        frame = img.crop((left, top, right, bottom)).resize(
            (img_width, img_height), Image.LANCZOS
        )

        # Convert the frame to a numpy array and add to frames list
        frames.append(np.array(frame))

    # Create a video clip from the frames
    clip = mpy.ImageSequenceClip(frames, fps=fps)

    # Write the result to a video file
    clip.write_videofile(output_video_path, codec="libx264")


# Example usage
ken_burns_effect(
    "picture.jpg", "ken_burns_effect.mp4", duration=5, zoom_factor=1.2, fps=30
)
