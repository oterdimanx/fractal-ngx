#!/usr/bin/env python3
"""
Fractal Journey Builder
Edit the journey_config below to create your own fractal animations
"""

import sys
import os

# Make sure we can import fractal_engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fractal_engine import FractalEngine, JourneyRenderer

# ========== EDIT THIS SECTION FOR YOUR JOURNEY ==========
journey_config = {
    "name": "needle_mini_with_turn",
    "fps": 24,
    "waypoints": [
        # Levels 1-4 (up to 4298.66x)
        {"type": "straight", "center": [-1.999, 0.0], "start_zoom": 1.0, "end_zoom": 10.0, "duration": 2, "max_iter": 100},
        {"type": "straight", "center": [-1.999, 0.0], "start_zoom": 10.0, "end_zoom": 100.0, "duration": 3, "max_iter": 200},
        {"type": "straight", "center": [-1.999, 0.0], "start_zoom": 100.0, "end_zoom": 1000.0, "duration": 4, "max_iter": 500},
        {"type": "straight", "center": [-1.999, 0.0], "start_zoom": 1000.0, "end_zoom": 4298.66, "duration": 4, "max_iter": 1000},

        # Turn
        {"type": "turn", "start_center": [-1.999, 0.0], "end_center": [-1.999096038222, -0.000000010721], "start_zoom": 4298.66, "end_zoom": 10000.0, "duration": 8, "curve_strength": 0.2},
        
        {"type": "straight", "center": [-1.999096038222, -0.000000010721], "start_zoom": 10000.0, "end_zoom": 100000.0, "duration": 4, "max_iter": 2000},
        {"type": "straight", "center": [-1.999096038222, -0.000000010721], "start_zoom": 100000.0, "end_zoom": 1000000.0, "duration": 4, "max_iter": 4000},
        {"type": "straight", "center": [-1.999096038222, -0.000000010721], "start_zoom": 1000000.0, "end_zoom": 100000000000.0, "duration": 10, "max_iter": 128000},
    ]
}

# ========== NO EDITING NEEDED BELOW THIS LINE ==========

if __name__ == "__main__":
    print("\n" + "="*60)
    print("FRACTAL JOURNEY BUILDER")
    print("="*60)
    print(f"Journey: {journey_config['name']}")
    print(f"Waypoints: {len(journey_config['waypoints'])}")
    
    # Show waypoint details
    for i, wp in enumerate(journey_config['waypoints']):
        if wp['type'] == 'straight':
            print(f"  {i+1}. Straight: {wp['start_zoom']:.0f}x → {wp['end_zoom']:.0f}x ({wp['duration']}s)")
        else:
            print(f"  {i+1}. Turn: {wp['start_zoom']:.0f}x → {wp['end_zoom']:.0f}x ({wp['duration']}s)")
    
    # Get resolution from config or use defaults
    width = journey_config.get("width", 1280)
    height = journey_config.get("height", 960)
    
    print(f"\nResolution: {width}×{height}")
    print(f"\nPress Ctrl+C to pause (will resume later)")
    print(f"Every frame is saved")
    print("="*60 + "\n")
    
    # Initialize engine and renderer
    engine = FractalEngine(width=width, height=height)
    renderer = JourneyRenderer(engine, output_dir="outputs")
    
    # Start rendering
    renderer.render_journey(journey_config, resume=True)