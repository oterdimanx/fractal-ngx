import numpy as np
from PIL import Image
import colorsys
import os
import json
import glob
from datetime import datetime

class FractalEngine:
    def __init__(self, width=1280, height=960):
        self.width = width
        self.height = height
        self.aspect = height / width
        
    def mandelbrot(self, x, y, max_iter):
        c = complex(x, y)
        z = 0
        for n in range(max_iter):
            if abs(z) > 2:
                return n
            z = z*z + c
        return max_iter
    
    def render_frame(self, center_x, center_y, zoom, max_iter):
        width_zoom = 3.0 / zoom
        xmin = center_x - width_zoom/2
        xmax = center_x + width_zoom/2
        ymin = center_y - width_zoom/2 * self.aspect
        ymax = center_y + width_zoom/2 * self.aspect
        
        img_array = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        x_vals = np.linspace(xmin, xmax, self.width)
        y_vals = np.linspace(ymin, ymax, self.height)
        
        for y_idx, y in enumerate(y_vals):
            for x_idx, x in enumerate(x_vals):
                iter_count = self.mandelbrot(x, y, max_iter)
                if iter_count == max_iter:
                    color = (0, 0, 0)
                else:
                    hue = (iter_count * 10) % 360 / 360.0
                    rgb = colorsys.hsv_to_rgb(hue, 0.8, 1.0)
                    color = tuple(int(c * 255) for c in rgb)
                img_array[y_idx, x_idx] = color
        
        return Image.fromarray(img_array)

class JourneyRenderer:
    def __init__(self, engine, output_dir="outputs"):
        self.engine = engine
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def render_journey(self, journey_config, resume=True):
        name = journey_config["name"]
        fps = journey_config.get("fps", 24)
        waypoints = journey_config["waypoints"]
        
        # Setup directories
        journey_dir = os.path.join(self.output_dir, name)
        frames_dir = os.path.join(journey_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        config_path = os.path.join(journey_dir, "config.json")
        
        # Calculate total frames expected
        total_frames_expected = 0
        for wp in waypoints:
            total_frames_expected += int(wp["duration"] * fps)
        
        # Load or create progress file
        progress_path = os.path.join(journey_dir, "progress.txt")
        start_frame = 0
        
        if resume and os.path.exists(progress_path):
            with open(progress_path, 'r') as f:
                start_frame = int(f.read().strip())
            print(f"🔄 Resuming from frame {start_frame}/{total_frames_expected}")
        
        # Save config immediately
        config = {
            "name": name,
            "fps": fps,
            "waypoints": waypoints,
            "total_frames_expected": total_frames_expected,
            "started_at": datetime.now().isoformat(),
            "status": "in_progress"
        }
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"Journey: {name}")
        print(f"Total frames expected: {total_frames_expected}")
        print(f"Starting from frame: {start_frame}")
        print(f"{'='*60}\n")
        
        # Load already rendered frames
        all_frames = []
        existing_frames = sorted(glob.glob(f"{frames_dir}/frame_*.png"))
        for f in existing_frames:
            frame_num = int(os.path.basename(f).split('_')[1].split('.')[0])
            if frame_num < start_frame:
                try:
                    all_frames.append(Image.open(f))
                except:
                    pass
        
        current_frame = len(all_frames)
        
        if current_frame > 0:
            print(f"📂 Loaded {current_frame} existing frames")
        
        # If we're already at or beyond total, just assemble
        if current_frame >= total_frames_expected:
            print("✅ All frames already rendered!")
            return self._assemble_gif(all_frames, journey_dir, name, fps, config)
        
        # Render remaining frames
        frame_counter = current_frame
        
        for wp_idx, waypoint in enumerate(waypoints):
            wp_frames = int(waypoint["duration"] * fps)
            
            # Skip this waypoint if we've already rendered past it
            if frame_counter >= wp_frames:
                frame_counter -= wp_frames
                continue
            
            print(f"\n--- Waypoint {wp_idx + 1}: {waypoint['type'].upper()} ---")
            print(f"   Starting at frame offset {frame_counter} of {wp_frames}")
            
            if waypoint["type"] == "straight":
                frame_counter = self._render_straight(
                    waypoint, frame_counter, wp_frames, frames_dir, all_frames, fps, current_frame
                )
            elif waypoint["type"] == "turn":
                frame_counter = self._render_turn(
                    waypoint, frame_counter, wp_frames, frames_dir, all_frames, fps, current_frame
                )
            
            current_frame = len(all_frames)
            
            # Save progress after each waypoint
            with open(progress_path, 'w') as f:
                f.write(str(current_frame))
            print(f"   💾 Progress saved: {current_frame}/{total_frames_expected} frames")
        
        return self._assemble_gif(all_frames, journey_dir, name, fps, config)
    
    def _render_straight(self, waypoint, frame_offset, wp_frames, frames_dir, all_frames, fps, start_global_frame):
        center_x, center_y = waypoint["center"]
        start_zoom = waypoint["start_zoom"]
        end_zoom = waypoint["end_zoom"]
        max_iter = waypoint.get("max_iter", 1000)
        
        rendered = 0
        
        for local_frame in range(frame_offset, wp_frames):
            global_frame = start_global_frame + rendered
            frame_path = f"{frames_dir}/frame_{global_frame:06d}.png"
            
            t = local_frame / (wp_frames - 1) if wp_frames > 1 else 0
            current_zoom = start_zoom * (end_zoom / start_zoom) ** t
            
            if rendered % 10 == 0 or rendered == wp_frames - frame_offset - 1:
                print(f"  Straight: frame {global_frame} (zoom {current_zoom:.2e}x)")
            
            img = self.engine.render_frame(center_x, center_y, current_zoom, max_iter)
            img.save(frame_path)
            all_frames.append(img)
            rendered += 1
        
        print(f"  ✓ Rendered {rendered} frames")
        return 0  # Reset offset for next waypoint
    
    def _render_turn(self, waypoint, frame_offset, wp_frames, frames_dir, all_frames, fps, start_global_frame):
        start_x, start_y = waypoint["start_center"]
        end_x, end_y = waypoint["end_center"]
        start_zoom = waypoint["start_zoom"]
        end_zoom = waypoint["end_zoom"]
        curve_strength = waypoint.get("curve_strength", 0.5)
        
        # Bezier control point
        cx = start_x + (end_x - start_x) * curve_strength
        cy = start_y + (end_y - start_y) * curve_strength
        
        def bezier(t, p0, p1, p2):
            return (1-t)**2 * p0 + 2*(1-t)*t * p1 + t**2 * p2
        
        rendered = 0
        
        for local_frame in range(frame_offset, wp_frames):
            global_frame = start_global_frame + rendered
            frame_path = f"{frames_dir}/frame_{global_frame:06d}.png"
            
            t = local_frame / (wp_frames - 1) if wp_frames > 1 else 0
            
            current_x = bezier(t, start_x, cx, end_x)
            current_y = bezier(t, start_y, cy, end_y)
            current_zoom = start_zoom * (end_zoom / start_zoom) ** t
            current_iter = int(1000 + (8000 - 1000) * t)
            
            if rendered % 10 == 0 or rendered == wp_frames - frame_offset - 1:
                print(f"  Turn: frame {global_frame} (t={t:.3f}, zoom {current_zoom:.2e}x)")
            
            img = self.engine.render_frame(current_x, current_y, current_zoom, current_iter)
            img.save(frame_path)
            all_frames.append(img)
            rendered += 1
        
        print(f"  ✓ Rendered {rendered} frames")
        return 0  # Reset offset for next waypoint
    
    def _assemble_gif(self, all_frames, journey_dir, name, fps, config):
        if len(all_frames) == 0:
            print("No frames to assemble!")
            return None
        
        output_gif = os.path.join(journey_dir, f"{name}.gif")
        print(f"\n📦 Assembling {len(all_frames)} frames into GIF...")
        
        all_frames[0].save(output_gif,
                           save_all=True,
                           append_images=all_frames[1:],
                           duration=int(1000/fps),
                           loop=0,
                           optimize=False)
        
        gif_size = os.path.getsize(output_gif) / (1024 * 1024)
        
        # Update config as completed
        config["completed_at"] = datetime.now().isoformat()
        config["status"] = "completed"
        config["total_frames_rendered"] = len(all_frames)
        config["gif_size_mb"] = round(gif_size, 1)
        
        config_path = os.path.join(journey_dir, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\nJourney complete!")
        print(f"   GIF: {output_gif} ({gif_size:.1f} MB)")
        print(f"   Frames: {len(all_frames)}")
        
        # Delete progress file on successful completion
        progress_path = os.path.join(journey_dir, "progress.txt")
        if os.path.exists(progress_path):
            os.remove(progress_path)
        
        return all_frames


class CoordinatePicker:
    """Utility class to pick fractal coordinates from rendered frames"""
    
    @staticmethod
    def get_frame_parameters(journey_dir, frame_number):
        """Reconstruct camera parameters at a given frame"""
        config_path = os.path.join(journey_dir, "config.json")
        
        if not os.path.exists(config_path):
            print(f"Config not found: {config_path}")
            print("   Make sure the journey has been started (even partially)")
            return None
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        fps = config.get("fps", 24)
        waypoints = config["waypoints"]
        
        frames_so_far = 0
        
        for wp in waypoints:
            duration = wp.get("duration", 0)
            wp_frames = int(duration * fps)
            
            if frame_number < frames_so_far + wp_frames:
                frame_in_wp = frame_number - frames_so_far
                t = frame_in_wp / wp_frames if wp_frames > 0 else 0
                
                if wp["type"] == "straight":
                    center_x, center_y = wp["center"]
                    start_zoom = wp["start_zoom"]
                    end_zoom = wp["end_zoom"]
                    current_zoom = start_zoom * (end_zoom / start_zoom) ** t
                    return center_x, center_y, current_zoom
                    
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
        
        print(f"Frame {frame_number} exceeds journey length (total frames: {frames_so_far})")
        return None
    
    @staticmethod
    def pixel_to_fractal(journey_dir, frame_number, pixel_x, pixel_y, width, height):
        """Convert pixel coordinates to fractal coordinates"""
        params = CoordinatePicker.get_frame_parameters(journey_dir, frame_number)
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
        
        print(f"\n{'='*60}")
        print(f"🎯 COORDINATE PICKER")
        print(f"{'='*60}")
        print(f"Journey: {os.path.basename(journey_dir)}")
        print(f"Frame: {frame_number}")
        print(f"Pixel: ({pixel_x}, {pixel_y})")
        print(f"Resolution: {width}×{height}")
        print(f"Zoom at this frame: {current_zoom:.2e}x")
        print(f"Center at this frame: ({center_x:.12f}, {center_y:.12f})")
        print(f"\n📌 FRACTAL COORDINATES for your turn:")
        print(f"   X = {fractal_x:.12f}")
        print(f"   Y = {fractal_y:.12f}")
        print(f"{'='*60}\n")
        
        return fractal_x, fractal_y, current_zoom