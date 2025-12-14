import customtkinter as ctk
from tkinter import filedialog
from PIL import Image

# -----------------------------------------------------------
# COLORS
# -----------------------------------------------------------
BG_COLOR = "#d0f2e8"
BOX_COLOR = "#a6c1b9"
BUTTON_LEFT = "#1ba6a6"
BUTTON_RIGHT = "#aee8ed"
TEXT_COLOR = "black"

# -----------------------------------------------------------
# IMAGE STORAGE
# -----------------------------------------------------------
loaded_image_pil = None
loaded_image_ctk = None
MAX_GUIDE_IMG = 350

# State for glitch-free resizing
content_hidden = False
resize_after_id = None

# State for instant window shrink fix
is_window_resizing = False
window_resize_id = None


# -----------------------------------------------------------
# DISPLAY IMAGE IN GUIDE BOX
# -----------------------------------------------------------
def display_image_in_guidebox():
    global loaded_image_pil, loaded_image_ctk

    if loaded_image_pil is None:
        return

    box_w = guide_box.winfo_width()
    box_h = guide_box.winfo_height()

    if box_w < 40 or box_h < 40:
        return

    img_w, img_h = loaded_image_pil.size
    scale = min(box_w / img_w, box_h / img_h)

    new_w = int(img_w * scale)
    new_h = int(img_h * scale)

    new_w = min(new_w, MAX_GUIDE_IMG)
    new_h = min(new_h, MAX_GUIDE_IMG)

    resized = loaded_image_pil.resize((new_w, new_h), Image.LANCZOS)
    loaded_image_ctk = ctk.CTkImage(light_image=resized, size=(new_w, new_h))

    guide_image_label.configure(image=loaded_image_ctk)


# -----------------------------------------------------------
# SELECT IMAGE
# -----------------------------------------------------------
def select_image():
    global loaded_image_pil

    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.webp")]
    )
    if not file_path:
        return

    loaded_image_pil = Image.open(file_path)
    display_image_in_guidebox()


# -----------------------------------------------------------
# MAIN SETUP
# -----------------------------------------------------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("IntelliPixel")
app.configure(fg_color=BG_COLOR)

# -----------------------------------------------------------
# OPTION 3 — LARGE fallback + instant maximize
# -----------------------------------------------------------
app.geometry("1600x900")     # fallback big size
app.update_idletasks()       # prevents small-window flash
app.state("zoomed")          # maximize instantly


# -----------------------------------------------------------
# CONTENT FRAME (HIDDEN DURING RESIZE)
# -----------------------------------------------------------
content_frame = ctk.CTkFrame(app, fg_color=BG_COLOR)
content_frame.grid(row=0, column=0, sticky="nsew")
app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(0, weight=1)


# -----------------------------------------------------------
# LAYOUT INSIDE CONTENT FRAME
# -----------------------------------------------------------
content_frame.grid_columnconfigure(0, weight=1)
content_frame.grid_columnconfigure(1, weight=8)
content_frame.grid_columnconfigure(2, weight=1)
content_frame.grid_rowconfigure(1, weight=1)

title_label = ctk.CTkLabel(content_frame, text="IntelliPixel", font=("Georgia", 32, "bold"))

# LEFT SIDE
left_panel = ctk.CTkFrame(content_frame, fg_color=BG_COLOR)
left_panel.grid_columnconfigure(0, weight=1)
left_panel.grid_rowconfigure(0, weight=1)

guide_box = ctk.CTkFrame(left_panel, fg_color=BOX_COLOR, corner_radius=30)
guide_image_label = ctk.CTkLabel(guide_box, text="")
guide_image_label.pack(expand=True)

select_btn = ctk.CTkButton(left_panel, text="Select image", fg_color=BUTTON_LEFT,
                           text_color="black", command=select_image)

export_btn = ctk.CTkButton(left_panel, text="Export", fg_color=BUTTON_LEFT,
                           text_color="black")

# CENTER
center_panel = ctk.CTkFrame(content_frame, fg_color=BG_COLOR)
center_panel.grid_columnconfigure(0, weight=1)
center_panel.grid_rowconfigure(0, weight=1)

image_box = ctk.CTkFrame(center_panel, fg_color=BOX_COLOR, corner_radius=40)

# RIGHT SIDE
right_panel = ctk.CTkFrame(content_frame, fg_color=BG_COLOR)
right_panel.grid_columnconfigure(0, weight=1)

remove_btn = ctk.CTkButton(right_panel, text="Object removal tool",
                           fg_color=BUTTON_RIGHT, text_color="black")
denoise_btn = ctk.CTkButton(right_panel, text="Image denoising",
                            fg_color=BUTTON_RIGHT, text_color="black")

low_label = ctk.CTkLabel(right_panel, text="Low light enhancement",
                         font=("Georgia", 20, "bold"))
low_slider = ctk.CTkSlider(right_panel)

tone_label = ctk.CTkLabel(right_panel, text="Artistic color tone",
                          font=("Georgia", 20, "bold"))
tone_slider = ctk.CTkSlider(right_panel)

preset_menu = ctk.CTkOptionMenu(right_panel,
                                values=["Preset 1", "Preset 2", "Preset 3", "Preset 4"],
                                fg_color=BUTTON_RIGHT, text_color="black")

search_entry = ctk.CTkEntry(content_frame, placeholder_text="Ask IntelliPixel…", fg_color="white")


# -----------------------------------------------------------
# GRID PLACEMENT
# -----------------------------------------------------------
title_label.grid(row=0, column=0, columnspan=3, pady=10)

left_panel.grid(row=1, column=0, sticky="nsew", padx=20)
guide_box.grid(row=0, column=0, sticky="nsew", pady=10)
select_btn.grid(row=1, column=0, sticky="ew", pady=5)
export_btn.grid(row=2, column=0, sticky="ew", pady=5)

center_panel.grid(row=1, column=1, sticky="nsew", padx=20)
image_box.grid(row=0, column=0, sticky="nsew")

right_panel.grid(row=1, column=2, sticky="nsew", padx=20)
remove_btn.grid(row=0, column=0, sticky="ew", pady=5)
denoise_btn.grid(row=1, column=0, sticky="ew", pady=5)
low_label.grid(row=2, column=0, sticky="w")
low_slider.grid(row=3, column=0, sticky="ew", pady=5)
tone_label.grid(row=4, column=0, sticky="w")
tone_slider.grid(row=5, column=0, sticky="ew", pady=5)
preset_menu.grid(row=6, column=0, sticky="e", pady=5)

search_entry.grid(row=2, column=0, columnspan=3, sticky="ew", padx=250, pady=25)


# -----------------------------------------------------------
# RESIZING LOGIC (NO GLITCHES)
# -----------------------------------------------------------
def resize_ui():
    w = app.winfo_width()
    h = app.winfo_height()
    scale = min(w / 1600, h / 900)

    title_label.configure(font=("Georgia", int(32 * scale), "bold"))
    low_label.configure(font=("Georgia", int(20 * scale), "bold"))
    tone_label.configure(font=("Georgia", int(20 * scale), "bold"))

    for btn in [select_btn, export_btn, remove_btn, denoise_btn]:
        btn.configure(height=int(45 * scale),
                      corner_radius=int(30 * scale),
                      font=("Arial", int(16 * scale)))

    search_entry.configure(height=int(45 * scale),
                           corner_radius=int(25 * scale),
                           font=("Arial", int(16 * scale)))

    display_image_in_guidebox()


def finish_resize():
    global content_hidden
    content_hidden = False
    content_frame.grid()
    resize_ui()


def on_resize(event):
    global resize_after_id, content_hidden

    if not content_hidden:
        content_hidden = True
        content_frame.grid_remove()

    if resize_after_id:
        app.after_cancel(resize_after_id)

    resize_after_id = app.after(120, finish_resize)


# -----------------------------------------------------------
# INSTANT WINDOW SHRINK FIX
# -----------------------------------------------------------
def freeze_window_resize(event):
    global is_window_resizing, window_resize_id

    if not is_window_resizing:
        is_window_resizing = True
        app.update_idletasks()
        app.grid_propagate(False)

    if window_resize_id:
        app.after_cancel(window_resize_id)

    window_resize_id = app.after(100, apply_final_window_size)


def apply_final_window_size():
    global is_window_resizing
    is_window_resizing = False

    app.grid_propagate(True)
    app.update_idletasks()


# -----------------------------------------------------------
# BINDINGS
# -----------------------------------------------------------
app.bind("<Configure>", freeze_window_resize)
app.bind("<Configure>", on_resize, add="+")

guide_box.bind("<Configure>", lambda e: display_image_in_guidebox())


# -----------------------------------------------------------
app.mainloop()
