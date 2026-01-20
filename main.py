import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

import numpy as np
import cv2
import sys
import os

# --- IMPORTS ---
import src.Other.bkgr as bkgr
import src.Other.flip as flip
import src.Llie.Llie as llie
import src.Filtering.apply as filtering
from src.Denoising.denoising import apply_auto_denoising_logic, apply_denoising_logic

# Try importing the C++ Object Remover
try:
    import ObjectRemover_core
    HAS_CPP_REMOVER = True
except ImportError:
    HAS_CPP_REMOVER = False

# -----------------------------------------------------------
# COLORS
# -----------------------------------------------------------
BG_COLOR = "#d0f2e8"
BOX_COLOR = "#a6c1b9"
BUTTON_LEFT = "#1ba6a6"
BUTTON_RIGHT = "#aee8ed"
TEXT_COLOR = "black"

# -----------------------------------------------------------
# STATE
# -----------------------------------------------------------
loaded_image_pil = None
loaded_image_path = None
edited_image_pil = None

# Resizing State
last_width = 1600
last_height = 900
resize_after_id = None
is_window_resizing = False
window_resize_id = None

# Denoise UI state
denoise_controls_visible = False
denoise_update_after_id = None 

# LLIE UI state
llie_controls_visible = False
llie_update_after_id = None 

# Filter UI state
filter_update_after_id = None

# View Swap State
is_view_swapped = False

# Object Removal State
roi_start = None
roi_end = None
is_selecting = False
remover = ObjectRemover_core.PatchRemover() if HAS_CPP_REMOVER else None


# -----------------------------------------------------------
# HELPERS
# -----------------------------------------------------------
def pil_to_cv2_bgr(pil_img: Image.Image) -> np.ndarray:
    if pil_img.mode == "RGBA": pil_img = pil_img.convert("RGB")
    elif pil_img.mode != "RGB": pil_img = pil_img.convert("RGB")
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def cv2_to_pil(cv_img: np.ndarray) -> Image.Image:
    if cv_img is None: raise ValueError("cv_img is None")
    return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))

def get_current_image_pil() -> Image.Image:
    return edited_image_pil if edited_image_pil is not None else loaded_image_pil

def ensure_image_loaded() -> bool:
    if loaded_image_pil is None:
        messagebox.showwarning("No image", "Please select an image first.")
        return False
    return True

# -----------------------------------------------------------
# DISPLAY LOGIC (SWAP + DYNAMIC FIT)
# -----------------------------------------------------------
def toggle_view_swap(event=None):
    """Swaps the Original and Edited images between Left and Center boxes."""
    global is_view_swapped
    if loaded_image_pil is None: return
    is_view_swapped = not is_view_swapped
    display_image_in_guidebox()
    display_image_in_centerbox()

def display_image_in_guidebox():
    if loaded_image_pil is None:
        guide_image_label.configure(image=None, text="")
        return
    
    # Logic: If swapped, show Result here. Else show Original.
    if is_view_swapped:
        img = edited_image_pil if edited_image_pil is not None else loaded_image_pil
    else:
        img = loaded_image_pil

    _display_image(img, guide_box, guide_image_label)

def display_image_in_centerbox():
    current_result = edited_image_pil if edited_image_pil is not None else loaded_image_pil
    if current_result is None:
        center_image_label.configure(image=None, text="Edited image will appear here")
        return

    # Logic: If swapped, show Original here. Else show Result.
    if is_view_swapped:
        img_to_show = loaded_image_pil
    else:
        img_to_show = current_result

    _display_image(img_to_show, image_box, center_image_label)

def _display_image(pil_img, box_widget, label_widget):
    # 1. Get container size
    box_w = box_widget.winfo_width()
    box_h = box_widget.winfo_height()

    if box_w < 50 or box_h < 50: return

    # Padding logic (20px margin per side)
    target_w = max(10, box_w - 40)
    target_h = max(10, box_h - 40)

    # 2. Scale image to FIT inside the padding
    img_w, img_h = pil_img.size
    scale = min(target_w / img_w, target_h / img_h)

    new_w = int(img_w * scale)
    new_h = int(img_h * scale)

    # 3. Resize and Display
    resized = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    ctk_img = ctk.CTkImage(light_image=resized, size=(new_w, new_h))
    
    label_widget.configure(image=ctk_img, text="")
    label_widget.image = ctk_img

# -----------------------------------------------------------
# CORE ACTIONS
# -----------------------------------------------------------
def select_image():
    global loaded_image_pil, loaded_image_path, edited_image_pil
    path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.webp")])
    if not path: return

    loaded_image_path = path
    loaded_image_pil = Image.open(path)
    edited_image_pil = None
    
    # Reset All Controls
    denoise_strength_slider.set(0)
    denoise_strength_value.configure(text="0")
    
    llie_int_slider.set(0)
    llie_int_value.configure(text="0")
    
    tone_slider.set(0)
    preset_menu.set("None")

    display_image_in_guidebox()
    display_image_in_centerbox()

def reset_image_action():
    global edited_image_pil
    if not ensure_image_loaded(): return
    edited_image_pil = None
    
    # Reset UI
    denoise_strength_slider.set(0)
    denoise_strength_value.configure(text="0")
    edge_preserving_switch.select()
    salt_pepper_switch.deselect()
    
    llie_int_slider.set(0)
    llie_int_value.configure(text="0")
    llie_det_slider.set(30)
    llie_clip_slider.set(2.0)
    
    tone_slider.set(0)
    preset_menu.set("None")
    
    display_image_in_centerbox()

def export_image():
    if not ensure_image_loaded(): return
    img = get_current_image_pil()
    path = filedialog.asksaveasfilename(defaultextension=".png")
    if path: img.save(path); messagebox.showinfo("Exported", f"Saved to:\n{path}")

def remove_background_action():
    global edited_image_pil
    if not ensure_image_loaded(): return
    try:
        base = get_current_image_pil()
        _, edited_image_pil = bkgr.run_background_removal(loaded_image_path, pil_image=base)
        display_image_in_centerbox()
    except Exception as e: messagebox.showerror("Error", str(e))

def flip_horizontal_action():
    global edited_image_pil
    if not ensure_image_loaded(): return
    edited_image_pil = flip.flip_horizontal(get_current_image_pil())
    display_image_in_centerbox()

def flip_vertical_action():
    global edited_image_pil
    if not ensure_image_loaded(): return
    edited_image_pil = flip.flip_vertical(get_current_image_pil())
    display_image_in_centerbox()

# -----------------------------------------------------------
# FILTERING (TONE & PRESETS)
# -----------------------------------------------------------
def schedule_filter_update(value=None):
    global filter_update_after_id
    if filter_update_after_id is not None:
        app.after_cancel(filter_update_after_id)
    filter_update_after_id = app.after(50, apply_filter_now)

def update_filter_preset(choice):
    if tone_slider.get() == 0 and choice != "None":
        tone_slider.set(50)
    apply_filter_now()

def apply_filter_now():
    global edited_image_pil, filter_update_after_id
    filter_update_after_id = None
    if not ensure_image_loaded(): return

    try:
        base_pil = loaded_image_pil
        cv_img = pil_to_cv2_bgr(base_pil)

        preset = preset_menu.get()
        intensity = tone_slider.get()

        if preset != "None" or intensity > 0:
            cv_img = filtering.apply_color_filter(cv_img, preset, intensity)

        edited_image_pil = cv2_to_pil(cv_img)
        display_image_in_centerbox()
    except Exception as e:
        messagebox.showerror("Filter Error", str(e))

# -----------------------------------------------------------
# DENOISING
# -----------------------------------------------------------
def toggle_denoise_controls():
    global denoise_controls_visible
    denoise_controls_visible = not denoise_controls_visible
    if denoise_controls_visible:
        denoise_controls_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
    else:
        denoise_controls_frame.grid_remove()

def denoise_auto_action():
    global edited_image_pil
    if not ensure_image_loaded(): return
    try:
        base = loaded_image_pil
        cv_img = pil_to_cv2_bgr(base)
        _, s, m, sp = apply_auto_denoising_logic(cv_img)
        
        denoise_strength_slider.set(s)
        denoise_strength_value.configure(text=str(int(s)))
        edge_preserving_switch.select() if m else edge_preserving_switch.deselect()
        salt_pepper_switch.select() if sp else salt_pepper_switch.deselect()
        
        edited_image_pil = cv2_to_pil(apply_denoising_logic(cv_img, s, m, sp))
        display_image_in_centerbox()
    except Exception as e: messagebox.showerror("Error", str(e))

def schedule_manual_denoise_update(val=None):
    global denoise_update_after_id
    if val: denoise_strength_value.configure(text=str(int(float(val))))
    if denoise_update_after_id: app.after_cancel(denoise_update_after_id)
    denoise_update_after_id = app.after(150, apply_manual_denoise_now)

def apply_manual_denoise_now():
    global edited_image_pil, denoise_update_after_id
    denoise_update_after_id = None
    if not ensure_image_loaded(): return
    try:
        base = loaded_image_pil
        cv_img = pil_to_cv2_bgr(base)
        s = int(denoise_strength_slider.get())
        if s > 0:
            m = bool(edge_preserving_var.get())
            sp = bool(salt_pepper_var.get())
            cv_img = apply_denoising_logic(cv_img, s, m, sp)
        edited_image_pil = cv2_to_pil(cv_img)
        display_image_in_centerbox()
    except Exception as e: print(e)

# -----------------------------------------------------------
# LOW LIGHT ENHANCEMENT (LLIE)
# -----------------------------------------------------------
def toggle_llie_controls():
    global llie_controls_visible
    llie_controls_visible = not llie_controls_visible
    if llie_controls_visible:
        llie_controls_frame.grid(row=4, column=0, sticky="ew", pady=(8, 0))
    else:
        llie_controls_frame.grid_remove()

def llie_auto_action():
    if not ensure_image_loaded(): return
    llie_int_slider.set(20)
    llie_det_slider.set(30)
    llie_clip_slider.set(2.0)
    llie_int_value.configure(text="20")
    apply_llie_now()

def schedule_llie_update(value=None):
    global llie_update_after_id
    if value: llie_int_value.configure(text=str(int(float(value))))
    if llie_update_after_id is not None: app.after_cancel(llie_update_after_id)
    llie_update_after_id = app.after(150, apply_llie_now)

def apply_llie_now():
    global edited_image_pil, llie_update_after_id
    llie_update_after_id = None
    if not ensure_image_loaded(): return

    try:
        base_pil = loaded_image_pil
        cv_img = pil_to_cv2_bgr(base_pil)

        intensity_val = llie_int_slider.get()
        if intensity_val > 0:
            intensity = intensity_val / 100.0
            detail = llie_det_slider.get() / 100.0
            clip = llie_clip_slider.get()
            cv_img = llie.enhance_image(cv_img, intensity=intensity, detail=detail, clahe_clip=clip)

        edited_image_pil = cv2_to_pil(cv_img)
        display_image_in_centerbox()
    except Exception as e: messagebox.showerror("Error", f"LLIE failed: {e}")

# -----------------------------------------------------------
# OBJECT REMOVAL
# -----------------------------------------------------------
def run_object_removal():
    global edited_image_pil, roi_start, roi_end
    if not HAS_CPP_REMOVER:
        messagebox.showerror("Error", "C++ Module Missing")
        return
    if not ensure_image_loaded() or not roi_start or not roi_end:
        messagebox.showwarning("Select", "Please draw a box first.")
        return

    # ROI Mapping Logic
    img = edited_image_pil if edited_image_pil else loaded_image_pil
    box_w, box_h = center_image_label.winfo_width(), center_image_label.winfo_height()
    
    target_w = max(10, box_w - 40)
    target_h = max(10, box_h - 40)
    scale = min(target_w / img.size[0], target_h / img.size[1])
    
    disp_w, disp_h = int(img.size[0] * scale), int(img.size[1] * scale)
    off_x, off_y = (box_w - disp_w) // 2, (box_h - disp_h) // 2
    
    x1, y1 = roi_start
    x2, y2 = roi_end
    rx = int((min(x1, x2) - off_x) / scale)
    ry = int((min(y1, y2) - off_y) / scale)
    rw = int(abs(x2 - x1) / scale)
    rh = int(abs(y2 - y1) / scale)

    if rw <= 0 or rh <= 0: return

    try:
        cv_img = pil_to_cv2_bgr(img)
        remover.set_image(cv_img)
        remover.set_selection(rx, ry, rw, rh)
        remover.process()
        edited_image_pil = cv2_to_pil(remover.get_result())
        roi_start = None
        display_image_in_centerbox()
    except Exception as e: print(e)

# Mouse Logic
def on_mouse_down(e):
    global roi_start, is_selecting
    if loaded_image_pil: is_selecting, roi_start = True, (e.x, e.y)
def on_mouse_drag(e):
    global roi_end
    if is_selecting: roi_end = (e.x, e.y); draw_selection()
def on_mouse_up(e):
    global is_selecting, roi_end
    is_selecting, roi_end = False, (e.x, e.y); draw_selection()

def draw_selection():
    img = edited_image_pil if edited_image_pil else loaded_image_pil
    if not img or not roi_start or not roi_end: return
    _display_image(img, image_box, center_image_label)

# -----------------------------------------------------------
# MAIN SETUP & LAYOUT
# -----------------------------------------------------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("IntelliPixel")
app.configure(fg_color=BG_COLOR)
app.geometry("1600x900")
app.update_idletasks()

if sys.platform.startswith("win"): app.state("zoomed")
elif sys.platform.startswith("linux"): app.attributes("-zoomed", True)
else: app.state("normal")

# CONTENT FRAME
content_frame = ctk.CTkFrame(app, fg_color=BG_COLOR)
content_frame.grid(row=0, column=0, sticky="nsew")
app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(0, weight=1)
content_frame.grid_columnconfigure(1, weight=8)
content_frame.grid_columnconfigure(2, weight=1)
content_frame.grid_rowconfigure(1, weight=1)

title_label = ctk.CTkLabel(content_frame, text="IntelliPixel", font=("Georgia", 32, "bold"))
title_label.grid(row=0, column=0, columnspan=3, pady=10)

# --- LEFT PANEL ---
left_panel = ctk.CTkFrame(content_frame, fg_color=BG_COLOR)
left_panel.grid(row=1, column=0, sticky="nsew", padx=20)
left_panel.grid_columnconfigure(0, weight=1)
left_panel.grid_rowconfigure(0, weight=1)

guide_box = ctk.CTkFrame(left_panel, fg_color=BOX_COLOR, corner_radius=30)
guide_box.grid(row=0, column=0, sticky="nsew", pady=10)
guide_image_label = ctk.CTkLabel(guide_box, text="")
guide_image_label.pack(expand=True)

# ADDED BINDING FOR SWAP
guide_image_label.bind("<Button-1>", toggle_view_swap)

select_btn = ctk.CTkButton(left_panel, text="Select image", fg_color=BUTTON_LEFT, text_color="black", command=select_image)
select_btn.grid(row=1, column=0, sticky="ew", pady=5)
export_btn = ctk.CTkButton(left_panel, text="Export", fg_color=BUTTON_LEFT, text_color="black", command=export_image)
export_btn.grid(row=2, column=0, sticky="ew", pady=5)

# --- CENTER PANEL ---
center_panel = ctk.CTkFrame(content_frame, fg_color=BG_COLOR)
center_panel.grid(row=1, column=1, sticky="nsew", padx=20)
center_panel.grid_columnconfigure(0, weight=1)
center_panel.grid_rowconfigure(0, weight=1)

image_box = ctk.CTkFrame(center_panel, fg_color=BOX_COLOR, corner_radius=40)
image_box.grid(row=0, column=0, sticky="nsew")
center_image_label = ctk.CTkLabel(image_box, text="Edited image will appear here")
center_image_label.pack(expand=True)

center_image_label.bind("<Button-1>", on_mouse_down)
center_image_label.bind("<B1-Motion>", on_mouse_drag)
center_image_label.bind("<ButtonRelease-1>", on_mouse_up)

# --- RIGHT PANEL ---
right_panel = ctk.CTkFrame(content_frame, fg_color=BG_COLOR)
right_panel.grid(row=1, column=2, sticky="nsew", padx=20)
right_panel.grid_columnconfigure(0, weight=1)

# 1. Object Removal
remove_btn = ctk.CTkButton(right_panel, text="Object removal tool", fg_color=BUTTON_RIGHT, text_color="black", command=run_object_removal)
remove_btn.grid(row=0, column=0, sticky="ew", pady=5)

# 2. Denoising
denoise_btn = ctk.CTkButton(right_panel, text="Image denoising", fg_color=BUTTON_RIGHT, text_color="black", command=toggle_denoise_controls)
denoise_btn.grid(row=1, column=0, sticky="ew", pady=5)

denoise_controls_frame = ctk.CTkFrame(right_panel, fg_color=BG_COLOR)
denoise_controls_frame.grid_columnconfigure(0, weight=1)
denoise_title = ctk.CTkLabel(denoise_controls_frame, text="Advanced Options", font=("Georgia", 18, "bold"), text_color=TEXT_COLOR)
denoise_title.grid(row=0, column=0, sticky="w", pady=(0, 6))
denoise_auto_btn = ctk.CTkButton(denoise_controls_frame, text="Auto Denoise", fg_color=BUTTON_RIGHT, text_color="black", command=denoise_auto_action)
denoise_auto_btn.grid(row=1, column=0, sticky="ew", pady=(0, 10))

str_row = ctk.CTkFrame(denoise_controls_frame, fg_color=BG_COLOR)
str_row.grid(row=2, column=0, sticky="ew")
str_row.grid_columnconfigure(0, weight=1)
denoise_strength_label = ctk.CTkLabel(str_row, text="Strength", font=("Georgia", 14, "bold"), text_color=TEXT_COLOR)
denoise_strength_label.grid(row=0, column=0, sticky="w")
denoise_strength_value = ctk.CTkLabel(str_row, text="0", font=("Arial", 12), text_color=TEXT_COLOR)
denoise_strength_value.grid(row=0, column=1, sticky="e")

denoise_strength_slider = ctk.CTkSlider(denoise_controls_frame, from_=0, to=30, command=schedule_manual_denoise_update)
denoise_strength_slider.set(0)
denoise_strength_slider.grid(row=3, column=0, sticky="ew", pady=(0, 10))

edge_preserving_var = ctk.IntVar(value=1)
edge_preserving_switch = ctk.CTkSwitch(denoise_controls_frame, text="Edge-Preserving", variable=edge_preserving_var, command=schedule_manual_denoise_update)
edge_preserving_switch.grid(row=4, column=0, sticky="w")
salt_pepper_var = ctk.IntVar(value=0)
salt_pepper_switch = ctk.CTkSwitch(denoise_controls_frame, text="Salt & Pepper Fix", variable=salt_pepper_var, command=schedule_manual_denoise_update)
salt_pepper_switch.grid(row=5, column=0, sticky="w")
denoise_controls_frame.grid_remove()

# 3. LLIE
llie_btn = ctk.CTkButton(right_panel, text="Low Light Enhance", fg_color=BUTTON_RIGHT, text_color="black", command=toggle_llie_controls)
llie_btn.grid(row=3, column=0, sticky="ew", pady=5)

llie_controls_frame = ctk.CTkFrame(right_panel, fg_color=BG_COLOR)
llie_controls_frame.grid_columnconfigure(0, weight=1)

llie_title = ctk.CTkLabel(llie_controls_frame, text="Advanced Options", font=("Georgia", 18, "bold"), text_color=TEXT_COLOR)
llie_title.grid(row=0, column=0, sticky="w", pady=(0, 6))

llie_auto_btn = ctk.CTkButton(llie_controls_frame, text="Auto Enhance", fg_color=BUTTON_RIGHT, text_color="black", command=llie_auto_action)
llie_auto_btn.grid(row=1, column=0, sticky="ew", pady=(0, 10))

llie_int_row = ctk.CTkFrame(llie_controls_frame, fg_color=BG_COLOR)
llie_int_row.grid(row=2, column=0, sticky="ew")
llie_int_row.grid_columnconfigure(0, weight=1)
ctk.CTkLabel(llie_int_row, text="Intensity", font=("Georgia", 14, "bold"), text_color=TEXT_COLOR).grid(row=0, column=0, sticky="w")
llie_int_value = ctk.CTkLabel(llie_int_row, text="0", font=("Arial", 12), text_color=TEXT_COLOR)
llie_int_value.grid(row=0, column=1, sticky="e")

llie_int_slider = ctk.CTkSlider(llie_controls_frame, from_=0, to=100, command=schedule_llie_update)
llie_int_slider.set(0)
llie_int_slider.grid(row=3, column=0, sticky="ew", pady=(0, 10))

ctk.CTkLabel(llie_controls_frame, text="Detail Strength", font=("Arial", 12), text_color=TEXT_COLOR).grid(row=4, column=0, sticky="w")
llie_det_slider = ctk.CTkSlider(llie_controls_frame, from_=0, to=100, command=schedule_llie_update)
llie_det_slider.set(30)
llie_det_slider.grid(row=5, column=0, sticky="ew", pady=(0, 10))

ctk.CTkLabel(llie_controls_frame, text="CLAHE Clip Limit", font=("Arial", 12), text_color=TEXT_COLOR).grid(row=6, column=0, sticky="w")
llie_clip_slider = ctk.CTkSlider(llie_controls_frame, from_=1.0, to=5.0, number_of_steps=40, command=schedule_llie_update)
llie_clip_slider.set(2.0)
llie_clip_slider.grid(row=7, column=0, sticky="ew", pady=(0, 5))

llie_controls_frame.grid_remove()

# 4. Other Buttons
bg_remove_btn = ctk.CTkButton(right_panel, text="Remove background", fg_color=BUTTON_RIGHT, text_color="black", command=remove_background_action)
bg_remove_btn.grid(row=5, column=0, sticky="ew", pady=5)

flip_h_btn = ctk.CTkButton(right_panel, text="Flip horizontal", fg_color=BUTTON_RIGHT, text_color="black", command=flip_horizontal_action)
flip_h_btn.grid(row=6, column=0, sticky="ew", pady=5)

flip_v_btn = ctk.CTkButton(right_panel, text="Flip vertical", fg_color=BUTTON_RIGHT, text_color="black", command=flip_vertical_action)
flip_v_btn.grid(row=7, column=0, sticky="ew", pady=5)

# 5. Tone & Filter
tone_label = ctk.CTkLabel(right_panel, text="Artistic color tone", font=("Georgia", 20, "bold"))
tone_label.grid(row=8, column=0, sticky="w", pady=(10,0))

tone_slider = ctk.CTkSlider(right_panel, from_=0, to=100, command=schedule_filter_update)
tone_slider.set(0)
tone_slider.grid(row=9, column=0, sticky="ew", pady=5)

preset_menu = ctk.CTkOptionMenu(right_panel, values=["None", "Warm", "Cool", "Sepia", "Cinematic", "Black & White"], fg_color=BUTTON_RIGHT, text_color="black", command=update_filter_preset)
preset_menu.grid(row=10, column=0, sticky="e", pady=5)

reset_btn = ctk.CTkButton(right_panel, text="Reset", fg_color=BUTTON_RIGHT, text_color="black", command=reset_image_action)
reset_btn.grid(row=11, column=0, sticky="ew", pady=(25, 5))

# -----------------------------------------------------------
# RESIZING LOGIC
# -----------------------------------------------------------
def resize_ui():
    w, h = app.winfo_width(), app.winfo_height()
    scale = min(w / 1600, h / 900)
    scale = max(0.5, min(1.5, scale))

    title_label.configure(font=("Georgia", int(32 * scale), "bold"))
    tone_label.configure(font=("Georgia", int(20 * scale), "bold"))
    denoise_title.configure(font=("Georgia", int(18 * scale), "bold"))
    llie_title.configure(font=("Georgia", int(18 * scale), "bold"))

    btn_height = int(45 * scale)
    btn_radius = int(30 * scale)
    btn_font = ("Arial", int(16 * scale))

    for btn in [select_btn, export_btn, remove_btn, denoise_btn, denoise_auto_btn,
                llie_btn, llie_auto_btn, bg_remove_btn, flip_h_btn, flip_v_btn, reset_btn]:
        btn.configure(height=btn_height, corner_radius=btn_radius, font=btn_font)

    display_image_in_guidebox()
    display_image_in_centerbox()

def on_resize(event):
    global last_width, last_height
    if 'last_width' not in globals(): last_width, last_height = 1600, 900
    cw, ch = app.winfo_width(), app.winfo_height()
    if cw == last_width and ch == last_height: return
    last_width, last_height = cw, ch
    resize_ui()

def freeze_window_resize(event):
    global is_window_resizing, window_resize_id
    if not is_window_resizing:
        is_window_resizing = True
        app.update_idletasks()
        app.grid_propagate(False)
    if window_resize_id: app.after_cancel(window_resize_id)
    window_resize_id = app.after(100, apply_final_window_size)

def apply_final_window_size():
    global is_window_resizing
    is_window_resizing = False
    app.grid_propagate(True)
    app.update_idletasks()

app.bind("<Configure>", freeze_window_resize)
app.bind("<Configure>", on_resize, add="+")
guide_box.bind("<Configure>", lambda e: display_image_in_guidebox())
image_box.bind("<Configure>", lambda e: display_image_in_centerbox())

app.mainloop()