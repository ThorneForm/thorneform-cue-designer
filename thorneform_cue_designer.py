import tkinter as tk
import json
from tkinter import filedialog
import os
from mutagen.mp3 import MP3
import miniaudio
import threading
import time



window = tk.Tk()
window.geometry("900x700")
window.minsize(900, 700)

window.title("ThorneForm LED Cue Designer")

title_label = tk.Label(window, text="ThorneForm LED Cue Designer")
title_label.pack(pady=5)
status_frame = tk.Frame(window, bg="#e8e8e8", relief="sunken", bd=1)
status_frame.pack(fill="x", padx=10, pady=5)

current_project_file = None


file_status_label = tk.Label(
    status_frame,
    text="File: No file loaded",
    bg="#e8e8e8",
    anchor="w"
)
file_status_label.pack(fill="x", padx=8)

timeline_status_label = tk.Label(
    status_frame,
    text="Cursor: 00:00.000        Length: 00:00.000",
    bg="#e8e8e8",
    anchor="w"
)
timeline_status_label.pack(fill="x", padx=8, pady=(0,2))

audio_title = tk.Label(
    window,
    text="Audio Track",
    font=("Segoe UI", 10, "bold")
)
audio_title.pack(pady=(8, 0))

audio_canvas = tk.Canvas(window, width=760, height=120, bg="white")
audio_canvas.pack(pady=5)

led_title = tk.Label(
    window,
    text="LED Track",
    font=("Segoe UI", 10, "bold")
)
led_title.pack(pady=(8, 0))

led_canvas = tk.Canvas(window, width=760, height=200, bg="white")
led_canvas.pack(pady=5)



LED_LEFT = 60
LED_RIGHT = 740
LED_TOP = 40
LED_BOTTOM = 180

playhead_x = LED_LEFT
audio_playhead = None
led_playhead = None

song_file = None
song_length_seconds = 0
current_song_name = "No file loaded"

is_playing = False
stop_requested = False
playback_start_time = None


preview_canvas = tk.Canvas(window, width=760, height=80, bg="white")
preview_canvas.pack(pady=5)

preview_circle = preview_canvas.create_oval(
    350, 15, 410, 75,
    fill="#003300",
    outline="black"
)

# # Draw fake audio waveform
# x = 40

# while x < 740:
#     audio_canvas.create_line(
#         x, 60, x + 10, 40,
#         fill="black",
#         tags="waveform"
#     )

#     audio_canvas.create_line(
#         x + 10, 40, x + 20, 80,
#         fill="black",
#         tags="waveform"
#     )

#     audio_canvas.create_line(
#         x + 20, 80, x + 30, 60,
#         fill="black",
#         tags="waveform"
#     )

#     x = x + 30

# Draw starting LED brightness line

POINT_RADIUS = 3

points = [
    [LED_LEFT, LED_BOTTOM],
    [LED_RIGHT, LED_BOTTOM]
]

selected_point = None

def clamp(value, minimum, maximum):
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value

def draw_led_scale():
    led_canvas.delete("scale")

    led_canvas.create_rectangle(
        LED_LEFT, LED_TOP, LED_RIGHT, LED_BOTTOM,
        outline="gray",
        tags="scale"
    )

    scale_marks = [
    ("100%", LED_TOP),
    ("75%", LED_TOP + (LED_BOTTOM - LED_TOP) * 0.25),
    ("50%", LED_TOP + (LED_BOTTOM - LED_TOP) * 0.50),
    ("25%", LED_TOP + (LED_BOTTOM - LED_TOP) * 0.75),
    ("0%", LED_BOTTOM)
]

    for label, y in scale_marks:
        led_canvas.create_text(LED_LEFT - 10, y, text=label, anchor="e", tags="scale")
        led_canvas.create_line(LED_LEFT, y, LED_RIGHT, y, fill="lightgray", tags="scale")

def draw_led_curve():
    led_canvas.delete("curve")
    draw_led_scale()

    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        led_canvas.create_line(x1, y1, x2, y2, fill="black", width=3, tags="curve")

    for x, y in points:
        led_canvas.create_oval(
            x - POINT_RADIUS,
            y - POINT_RADIUS,
            x + POINT_RADIUS,
            y + POINT_RADIUS,
            fill="black",
            outline="black",
            tags="curve"
        )
def find_point(x, y):
    for i, point in enumerate(points):
        px, py = point
        if abs(px - x) < 10 and abs(py - y) < 10:
            return i
    return None

def mouse_down(event):
    global selected_point

    clicked_point = find_point(event.x, event.y)

    if clicked_point is not None:
        selected_point = clicked_point
    else:
        new_x = clamp(event.x, LED_LEFT, LED_RIGHT)
        new_y = clamp(event.y, LED_TOP, LED_BOTTOM)

        points.append([new_x, new_y])
        points.sort()
        selected_point = find_point(new_x, new_y)
        draw_led_curve()

def mouse_drag(event):
    if selected_point is not None:
        new_x = clamp(event.x, LED_LEFT, LED_RIGHT)
        new_y = clamp(event.y, LED_TOP, LED_BOTTOM)

        points[selected_point][0] = new_x
        points[selected_point][1] = new_y

        points.sort()
        draw_led_curve()

def mouse_up(event):
    global selected_point
    selected_point = None

def delete_point(event):
    clicked_point = find_point(event.x, event.y)

    if clicked_point is not None and len(points) > 2:
        points.pop(clicked_point)
        draw_led_curve()

def draw_hover_line(x):
    hover_x = clamp(x, LED_LEFT, LED_RIGHT)

    audio_canvas.delete("hover_line")
    led_canvas.delete("hover_line")

    audio_canvas.create_line(
        hover_x, 5,
        hover_x, 115,
        fill="blue",
        dash=(4, 4),
        tags="hover_line"
    )

    led_canvas.create_line(
        hover_x, LED_TOP,
        hover_x, LED_BOTTOM,
        fill="blue",
        dash=(4, 4),
        tags="hover_line"
    )

def move_hover_line(event):
    draw_hover_line(event.x)

def clear_hover_line(event):
    audio_canvas.delete("hover_line")
    led_canvas.delete("hover_line")

led_canvas.bind("<Button-1>", mouse_down)
led_canvas.bind("<B1-Motion>", mouse_drag)
led_canvas.bind("<ButtonRelease-1>", mouse_up)
led_canvas.bind("<Button-3>", delete_point)
led_canvas.bind("<Motion>", move_hover_line)
led_canvas.bind("<Leave>", clear_hover_line)

draw_led_curve()




def y_to_brightness(y):
    brightness = int((LED_BOTTOM - y) / (LED_BOTTOM - LED_TOP) * 255)
    return clamp(brightness, 0, 255)

def brightness_to_green(brightness):
    green = int(brightness)
    return f"#00{green:02x}00"

def play_preview():
    global is_playing, stop_requested, playback_start_time

    if song_file is None:
        print("No MP3 loaded.")
        return

    if is_playing:
        return

    is_playing = True
    stop_requested = False
    playback_start_time = time.time()
    

    def audio_thread():
        global playback_start_time

        stream = miniaudio.stream_file(song_file)

        with miniaudio.PlaybackDevice() as device:
            playback_start_time = time.time()
            device.start(stream)

            while is_playing and not stop_requested:
                elapsed = time.time() - playback_start_time

                if elapsed >= song_length_seconds:
                    break

                time.sleep(0.05)

        print("Playback finished.")

    threading.Thread(
        target=audio_thread,
        daemon=True
    ).start()

    update_playhead_during_playback()

def x_to_time(x):    
    percent = (x - LED_LEFT) / (LED_RIGHT - LED_LEFT)
    time_value = percent * song_length_seconds
    return round(time_value, 2)

def export_timeline():
    if song_file is None:
        print("No MP3 loaded.")
        return

    timeline = []

    for x, y in sorted(points):
        timeline.append({
            "time": x_to_time(x),
            "brightness": y_to_brightness(y)
        })

    export_data = {
        "version": 1,
        "song": current_song_name,
        "duration": round(song_length_seconds, 3),
        "tracks": {
            "main": timeline
        }
    }

    os.makedirs("exports", exist_ok=True)

    file_path = filedialog.asksaveasfilename(
        title="Export Cue JSON",
        initialdir="exports",
        initialfile=current_song_name.replace(".mp3", "_cue.json"),
        defaultextension=".json",
        filetypes=[("JSON Files", "*.json")]
    )

    if not file_path:
        return

    with open(file_path, "w") as file:
        json.dump(export_data, file, indent=4)

    print(f"Exported: {file_path}")

def build_project_data():
    return {
        "project_name": "Untitled",
        "version": 1,
        "song_file": song_file,
        "song_name": current_song_name,
        "song_length": round(song_length_seconds, 3),
        "playhead_x": playhead_x,
        "points": points
    }


def save_project():
    global current_project_file

    if current_project_file is None:
        save_project_as()
        return

    project_data = build_project_data()

    with open(current_project_file, "w") as file:
        json.dump(project_data, file, indent=4)

    print(f"Saved project: {current_project_file}")


def save_project_as():
    global current_project_file

    os.makedirs("projects", exist_ok=True)

    file_path = filedialog.asksaveasfilename(
        title="Save Project As",
        initialdir="projects",
        defaultextension=".tfcue",
        filetypes=[("ThorneForm Cue Project", "*.tfcue")]
    )

    if not file_path:
        return

    current_project_file = file_path
    save_project()

def draw_audio_waveform(file_path):
    audio_canvas.delete("waveform")

    decoded = miniaudio.decode_file(
        file_path,
        output_format=miniaudio.SampleFormat.FLOAT32,
        nchannels=1
    )

    samples = decoded.samples
    sample_count = len(samples)

    waveform_left = LED_LEFT
    waveform_right = LED_RIGHT
    waveform_top = 8
    waveform_bottom = 112
    waveform_center = (waveform_top + waveform_bottom) / 2
    waveform_height = (waveform_bottom - waveform_top) / 2

    pixel_step = 2
    width = (waveform_right - waveform_left) // pixel_step

    samples_per_pixel = max(1, sample_count // width)

    amplitudes = []

    for i in range(width):
        start = i * samples_per_pixel
        end = start + samples_per_pixel
        chunk = samples[start:end]

        if not chunk:
            amplitudes.append(0)
        else:
            amplitudes.append(
                sum(abs(sample) for sample in chunk) / len(chunk)
            )
    max_amplitude = max(amplitudes)

    if max_amplitude == 0:
        max_amplitude = 1

    for i, amplitude in enumerate(amplitudes):
        normalized = (amplitude / max_amplitude) ** 1.5

        x = waveform_left + (i * pixel_step)
        y1 = waveform_center - normalized * waveform_height
        y2 = waveform_center + normalized * waveform_height

        audio_canvas.create_line(
            x, y1, x, y2,
            fill="black",
            width=2,
            tags="waveform"
        )

def load_mp3():
    global song_file, song_length_seconds, current_song_name

    file_path = filedialog.askopenfilename(
        title="Select MP3 File",
        filetypes=[("MP3 Files", "*.mp3")]
    )

    if file_path:
        song_file = file_path
        song_name = os.path.basename(song_file)
        current_song_name = song_name

        audio = MP3(song_file)
        song_length_seconds = audio.info.length
        update_status_bar()

                
        draw_audio_waveform(song_file)

        print(f"Loaded: {song_name}")
        print(f"Song length: {round(song_length_seconds, 2)} seconds")

def get_brightness_at_time(current_time):
    sorted_points = sorted(points)

    # Before first point
    first_time = x_to_time(sorted_points[0][0])
    if current_time <= first_time:
        return y_to_brightness(sorted_points[0][1])

    # After last point
    last_time = x_to_time(sorted_points[-1][0])
    if current_time >= last_time:
        return y_to_brightness(sorted_points[-1][1])

    # Between points
    for i in range(len(sorted_points) - 1):
        x1, y1 = sorted_points[i]
        x2, y2 = sorted_points[i + 1]

        t1 = x_to_time(x1)
        t2 = x_to_time(x2)

        if t1 <= current_time <= t2:
            b1 = y_to_brightness(y1)
            b2 = y_to_brightness(y2)

            percent = (current_time - t1) / (t2 - t1)

            brightness = b1 + percent * (b2 - b1)
            return int(brightness)

    return 0

def pause_preview():
    print("Pause not built yet.")

def stop_preview():
    global is_playing, stop_requested

    is_playing = False
    stop_requested = True

    draw_playhead(LED_LEFT)

    print("Stopped.")

def x_to_clock_time(x):
    seconds = x_to_time(x)

    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes:02d}:{remaining_seconds:06.3f}"

def seconds_to_clock_time(seconds):
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes:02d}:{remaining_seconds:06.3f}"

def update_status_bar():
    cursor_time = x_to_clock_time(playhead_x)
    length_time = seconds_to_clock_time(song_length_seconds)

    file_status_label.config(text=f"File: {current_song_name}")
    timeline_status_label.config(
        text=f"Cursor: {cursor_time}        Length: {length_time}"
    )

def draw_playhead(x):
    global playhead_x, audio_playhead, led_playhead

    playhead_x = clamp(x, LED_LEFT, LED_RIGHT)

    audio_canvas.delete("playhead")
    led_canvas.delete("playhead")

    audio_playhead = audio_canvas.create_line(
        playhead_x, 5,
        playhead_x, 115,
        fill="red",
        width=2,
        tags="playhead"
    )

    led_playhead = led_canvas.create_line(
        playhead_x, LED_TOP,
        playhead_x, LED_BOTTOM,
        fill="red",
        width=2,
        tags="playhead"
    )

    update_status_bar()

       
#     audio_canvas.delete("time_label")
#     audio_canvas.create_text(
#     playhead_x,
#     18,
#     text=time_text,
#     anchor="s",
#     fill="red",
#     font=("Segoe UI", 9, "bold"),
#     tags="time_label"
# )


def move_playhead(event):
    draw_playhead(event.x)
   

audio_canvas.bind("<Button-1>", move_playhead)
audio_canvas.bind("<B1-Motion>", move_playhead)

led_canvas.bind("<Shift-Button-1>", move_playhead)
led_canvas.bind("<Shift-B1-Motion>", move_playhead)

draw_playhead(LED_LEFT)

def update_playhead_during_playback():
    global is_playing

    if not is_playing:
        return

    elapsed = time.time() - playback_start_time

    if elapsed >= song_length_seconds:
        elapsed = song_length_seconds
        is_playing = False

    percent = elapsed / song_length_seconds
    new_x = LED_LEFT + percent * (LED_RIGHT - LED_LEFT)

    draw_playhead(new_x)
    brightness = get_brightness_at_time(elapsed)
    color = brightness_to_green(brightness)
    preview_canvas.itemconfig(preview_circle, fill=color)

    if is_playing:
        window.after(30, update_playhead_during_playback)

def load_project():
    global current_project_file
    global song_file
    global current_song_name
    global song_length_seconds
    global playhead_x
    global points

    file_path = filedialog.askopenfilename(
        title="Open Project",
        initialdir="projects",
        filetypes=[("ThorneForm Cue Project", "*.tfcue")]
    )

    if not file_path:
        return

    with open(file_path, "r") as file:
        project = json.load(file)

    current_project_file = file_path
    song_file = project["song_file"]
    current_song_name = project["song_name"]
    song_length_seconds = project["song_length"]
    playhead_x = project["playhead_x"]
    points = project["points"]

    draw_led_curve()
    draw_playhead(playhead_x)
    update_status_bar()

    if song_file:
        draw_audio_waveform(song_file)

    print(f"Loaded project: {current_project_file}")



button_frame = tk.Frame(window)
button_frame.pack(pady=10)

load_button = tk.Button(
    button_frame,
    text="Load MP3",
    command=load_mp3
)

load_button.pack(side="left", padx=5)

load_project_button = tk.Button(
    button_frame,
    text="Load Project",
    command=load_project
)
load_project_button.pack(side="left", padx=5)

save_button = tk.Button(
    button_frame,
    text="Save Project",
    command=save_project
)
save_button.pack(side="left", padx=5)

save_as_button = tk.Button(
    button_frame,
    text="Save As",
    command=save_project_as
)
save_as_button.pack(side="left", padx=5)

preview_button = tk.Button(
    button_frame,
    text="▶ Play",
    command=play_preview
)
preview_button.pack(side="left", padx=5)

pause_button = tk.Button(
    button_frame,
    text="⏸ Pause",
    command=pause_preview
)
pause_button.pack(side="left", padx=5)

stop_button = tk.Button(
    button_frame,
    text="■ Stop",
    command=stop_preview
)
stop_button.pack(side="left", padx=5)

export_button = tk.Button(
    button_frame,
    text="Export",
    command=export_timeline
)
export_button.pack(side="left", padx=5)


      
window.mainloop()