#!/usr/bin/env python3
"""
Find fractal coordinates from a rendered frame
Usage: python pick_coordinate.py <journey_name> <frame_number> <pixel_x> <pixel_y>
Example: python pick_coordinate.py needle_mini_two_turns 700 758 648
"""

import sys
import json
import os
import numpy as np
from PIL import Image

def get_frame_parameters(journey_dir, frame_number):
    """Reconstruct camera parameters at a given frame"""
    config_path = os.path.join(journey_dir, "config.json")
    
    if not os.path.exists(config_path):
        print(f"Config not found: {config_path}")
        return None
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    fps = config.get("fps", 24)
    waypoints = config["waypoints"]
    
    # Walk through waypoints to find where this frame is
    frames_so_far = 0
    
    for wp in waypoints:
        duration = wp.get("duration", 0)
        wp_frames = int(duration * fps)
        
        if frame_number < frames_so_far + wp_frames:
            # Found the right waypoint
            frame_in_wp = frame_number - frames_so_far
            t = frame_in_wp / wp_frames
            
            if wp["type"] == "straight":
                # Center is fixed
                center_x, center_y = wp["center"]
                start_zoom = wp["start_zoom"]
                end_zoom = wp["end_zoom"]
                current_zoom = start_zoom * (end_zoom / start_zoom) ** t
                
            else:  # turn
                start_x, start_y = wp["start_center"]
                end_x, end_y = wp["end_center"]
                start_zoom = wp["start_zoom"]
                end_zoom = wp["end_zoom"]
                
                curve_strength = wp.get("curve_strength", 0.5)
                cx = start_x + (end_x - start_x) * curve_strength
                cy = start_y + (end_y - start_y) * curve_strength
                
                def bezier(t, p0, p1, p2):
                    return (1-t)**2 * p0 + 2*(1-t)*t * p1 + t**2 * p2
                
                center_x = bezier(t, start_x, cx, end_x)
                center_y = bezier(t, start_y, cy, end_y)
                current_zoom = start_zoom * (end_zoom / start_zoom) ** t
            
            return center_x, center_y, current_zoom
        
        frames_so_far += wp_frames
    
    print(f"Frame {frame_number} exceeds journey length")
    return None


def pixel_to_fractal(journey_dir, frame_number, pixel_x, pixel_y, width, height):
    params = get_frame_parameters(journey_dir, frame_number)
    if not params:
        return None
    
    center_x, center_y, current_zoom = params
    
    aspect = height / width
    width_zoom = 3.0 / current_zoom
    xmin = center_x - width_zoom/2
    xmax = center_x + width_zoom/2
    ymin = center_y - width_zoom/2 * aspect
    ymax = center_y + width_zoom/2 * aspect
    
    fractal_x = xmin + (pixel_x / width) * (xmax - xmin)
    fractal_y = ymin + (pixel_y / height) * (ymax - ymin)
    
    print(f"\n{'='*50}")
    print(f"COORDINATE PICKER")
    print(f"{'='*50}")
    print(f"Journey: {os.path.basename(journey_dir)}")
    print(f"Frame: {frame_number}")
    print(f"Pixel: ({pixel_x}, {pixel_y})")
    print(f"Resolution: {width}×{height}")
    print(f"Zoom at this frame: {current_zoom:.2e}x")
    print(f"Center at this frame: ({center_x:.12f}, {center_y:.12f})")
    print(f"\n🎯 FRACTAL COORDINATES:")
    print(f"   X = {fractal_x:.12f}")
    print(f"   Y = {fractal_y:.12f}")
    print(f"{'='*50}\n")
    
    return fractal_x, fractal_y, current_zoom


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python pick_coordinate.py <journey_name> <frame> <pixel_x> <pixel_y>")
        print("Example: python pick_coordinate.py needle_mini_two_turns 700 758 648")
        sys.exit(1)
    
    journey_name = sys.argv[1]
    frame_number = int(sys.argv[2])
    pixel_x = int(sys.argv[3])
    pixel_y = int(sys.argv[4])
    
    journey_dir = f"outputs/{journey_name}"
    width, height = 1280, 960  # Match your render resolution
    
    pixel_to_fractal(journey_dir, frame_number, pixel_x, pixel_y, width, height)