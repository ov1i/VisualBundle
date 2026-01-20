# GUI.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

import numpy as np
import cv2
import sys
import os

import src.Other.bkgr as bkgr
import src.Other.flip as flip
from src.Denoising.denoising import apply_auto_denoising_logic, apply_denoising_logic

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
loaded_image_path = None

edited_image_pil = None
edited_image_ctk = None

MAX_GUIDE_IMG = 350
MAX_CENTER_IMG = 650

# State for glitch-free resizing
content_hidden = False
resize_after_id = None

# State for instant window shrink fix
is_window_resizing = False
window_resize_id = None

# Denoise UI state
denoise_controls_visible = False
denoise_update_after_id = None  # debounce


# -----------------------------------------------------------
# HELPERS: PIL <-> OpenCV
# -----------------------------------------------------------
def pil_to_cv2_bgr(pil_img: Image.Image) -> np.ndarray:
    """PIL (RGB/RGBA/L) -> OpenCV BGR or GRAY (uint8)."""
    if pil_img.mode == "RGBA":
        pil_img = pil_img.convert("RGB")
    elif pil_img.mode not in ("RGB", "L"):
        pil_img = pil_img.convert("RGB")

    arr = np.array(pil_img)
    if arr.ndim == 2:  # grayscale
        return arr
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def cv2_to_pil(cv_img: np.ndarray) -> Image.Image:
    """OpenCV BGR/GRAY -> PIL."""
    if cv_img is None:
        raise ValueError("cv_img is None")
    if cv_img.ndim == 2:
        return Image.fromarray(cv_img)
    rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


# -----------------------------------------------------------
# PIPELINE: always apply edits on the current image
# -----------------------------------------------------------
def get_current_image_pil() -> Image.Image:
    """Return edited image if exists, else original."""
    return edited_image_pil if edited_image_pil is not None else loaded_image_pil


def ensure_image_loaded() -> bool:
    if loaded_image_pil is None:
        messagebox.showwarning("No image", "Please select an image first.")
        return False
    return True


# -----------------------------------------------------------
# DISPLAY IMAGE IN GUIDE BOX (LEFT)
# -----------------------------------------------------------
def display_image_in_guidebox():
    global loaded_image_pil, loaded_image_ctk

    if loaded_image_pil is None:
        guide_image_label.configure(image=None, text="")
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
    guide_image_label.configure(image=loaded_image_ctk, text="")


# -----------------------------------------------------------
# DISPLAY IMAGE IN CENTER BOX (MIDDLE)
# -----------------------------------------------------------
def display_image_in_centerbox():
    global edited_image_pil, edited_image_ctk

    # If edited is None, show ORIGINAL in the middle (your new requirement)
    img_to_show = edited_image_pil if edited_image_pil is not None else loaded_image_pil

    if img_to_show is None:
        center_image_label.configure(image=None, text="Edited image will appear here")
        return

    box_w = image_box.winfo_width()
    box_h = image_box.winfo_height()
    if box_w < 60 or box_h < 60:
        return

    img_w, img_h = img_to_show.size
    scale = min(box_w / img_w, box_h / img_h)

    new_w = int(img_w * scale)
    new_h = int(img_h * scale)

    new_w = min(new_w, MAX_CENTER_IMG)
    new_h = min(new_h, MAX_CENTER_IMG)

    resized = img_to_show.resize((new_w, new_h), Image.LANCZOS)
    edited_image_ctk = ctk.CTkImage(light_image=resized, size=(new_w, new_h))
    center_image_label.configure(image=edited_image_ctk, text="")


# -----------------------------------------------------------
# SELECT IMAGE
# -----------------------------------------------------------
def select_image():
    global loaded_image_pil, loaded_image_path, edited_image_pil, edited_image_ctk

    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.webp")]
    )
    if not file_path:
        return

    loaded_image_path = file_path
    loaded_image_pil = Image.open(file_path)

    # reset edited
    edited_image_pil = None
    edited_image_ctk = None

    display_image_in_guidebox()
    display_image_in_centerbox()


# -----------------------------------------------------------
# RESET (back to original, and show original in middle)
# -----------------------------------------------------------
def reset_image_action():
    global edited_image_pil, edited_image_ctk

    if not ensure_image_loaded():
        return

    edited_image_pil = None
    edited_image_ctk = None

    # Reset denoise UI defaults too
    denoise_strength_slider.set(10)
    denoise_strength_value.configure(text="10")
    edge_preserving_switch.select()
    salt_pepper_switch.deselect()

    # Middle box should still show original
    display_image_in_centerbox()


# -----------------------------------------------------------
# BACKGROUND REMOVAL (applies to CURRENT image always)
# -----------------------------------------------------------
def remove_background_action():
    global edited_image_pil
    if not ensure_image_loaded():
        return
    try:
        base_img = get_current_image_pil()
        _, removed_bg = bkgr.run_background_removal(
            loaded_image_path, pil_image=base_img
        )
        edited_image_pil = removed_bg
        display_image_in_centerbox()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to remove background:\n{e}")


# -----------------------------------------------------------
# FLIP (applies to CURRENT image always)
# -----------------------------------------------------------
def flip_horizontal_action():
    global edited_image_pil
    if not ensure_image_loaded():
        return
    try:
        base_img = get_current_image_pil()
        edited_image_pil = flip.flip_horizontal(base_img)
        display_image_in_centerbox()
    except Exception as e:
        messagebox.showerror("Error", f"Flip failed:\n{e}")


def flip_vertical_action():
    global edited_image_pil
    if not ensure_image_loaded():
        return
    try:
        base_img = get_current_image_pil()
        edited_image_pil = flip.flip_vertical(base_img)
        display_image_in_centerbox()
    except Exception as e:
        messagebox.showerror("Error", f"Flip failed:\n{e}")


# -----------------------------------------------------------
# DENOISING UI + LOGIC (applies to CURRENT image always)
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
    if not ensure_image_loaded():
        return

    try:
        base_pil = get_current_image_pil()
        cv_img = pil_to_cv2_bgr(base_pil)

        result, strength, mode, sp_fix = apply_auto_denoising_logic(cv_img)
        if result is None:
            raise RuntimeError("Auto denoising returned None")

        strength = int(max(1, min(30, strength)))
        denoise_strength_slider.set(strength)
        denoise_strength_value.configure(text=str(strength))

        edge_preserving_switch.select() if bool(mode) else edge_preserving_switch.deselect()
        salt_pepper_switch.select() if bool(sp_fix) else salt_pepper_switch.deselect()

        edited_image_pil = cv2_to_pil(result)
        display_image_in_centerbox()

    except Exception as e:
        messagebox.showerror("Error", f"Auto denoising failed:\n{e}")


def schedule_manual_denoise_update(*_):
    global denoise_update_after_id
    if denoise_update_after_id is not None:
        app.after_cancel(denoise_update_after_id)
    denoise_update_after_id = app.after(180, apply_manual_denoise_now)


def apply_manual_denoise_now():
    global edited_image_pil, denoise_update_after_id
    denoise_update_after_id = None

    if not ensure_image_loaded():
        return

    try:
        base_pil = get_current_image_pil()
        cv_img = pil_to_cv2_bgr(base_pil)

        strength = int(round(denoise_strength_slider.get()))
        strength = max(1, min(30, strength))
        denoise_strength_value.configure(text=str(strength))

        edge_preserving = bool(edge_preserving_var.get())
        salt_pepper_fix = bool(salt_pepper_var.get())

        result = apply_denoising_logic(cv_img, strength, edge_preserving, salt_pepper_fix)
        if result is None:
            raise RuntimeError("Manual denoising returned None")

        edited_image_pil = cv2_to_pil(result)
        display_image_in_centerbox()

    except Exception as e:
        messagebox.showerror("Error", f"Manual denoising failed:\n{e}")


# -----------------------------------------------------------
# EXPORT
# -----------------------------------------------------------
def export_image():
    if loaded_image_pil is None:
        messagebox.showwarning("No image", "Please select an image first.")
        return

    # Export the CURRENT image (edited if exists, otherwise original)
    img_to_save = edited_image_pil if edited_image_pil is not None else loaded_image_pil

    out_path = filedialog.asksaveasfilename(
        title="Export image",
        defaultextension=".png",
        filetypes=[
            ("PNG", "*.png"),
            ("JPEG", "*.jpg *.jpeg"),
            ("WEBP", "*.webp"),
            ("BMP", "*.bmp"),
            ("All files", "*.*"),
        ],
    )
    if not out_path:
        return

    try:
        # If saving JPEG, must remove alpha channel
        lower = out_path.lower()
        if lower.endswith((".jpg", ".jpeg")):
            if img_to_save.mode in ("RGBA", "LA"):
                img_to_save = img_to_save.convert("RGB")
            img_to_save.save(out_path, format="JPEG", quality=95)
        elif lower.endswith(".webp"):
            img_to_save.save(out_path, format="WEBP", quality=95)
        elif lower.endswith(".bmp"):
            img_to_save.save(out_path, format="BMP")
        else:
            # Default PNG (keeps transparency if present)
            img_to_save.save(out_path, format="PNG")

        messagebox.showinfo("Exported", f"Saved to:\n{out_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Export failed:\n{e}")



# -----------------------------------------------------------
# MAIN SETUP
# -----------------------------------------------------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("IntelliPixel")
app.configure(fg_color=BG_COLOR)

app.geometry("1600x900")
app.update_idletasks()
if sys.platform.startswith("win"):
    app.state("zoomed")
elif sys.platform.startswith("linux"):
    app.attributes("-zoomed", True)
else:
    app.state("normal")

# -----------------------------------------------------------
# CONTENT FRAME
# -----------------------------------------------------------
content_frame = ctk.CTkFrame(app, fg_color=BG_COLOR)
content_frame.grid(row=0, column=0, sticky="nsew")
app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(0, weight=1)

content_frame.grid_columnconfigure(0, weight=1)
content_frame.grid_columnconfigure(1, weight=8)
content_frame.grid_columnconfigure(2, weight=1)
content_frame.grid_rowconfigure(1, weight=1)

title_label = ctk.CTkLabel(content_frame, text="IntelliPixel", font=("Georgia", 32, "bold"))

# LEFT
left_panel = ctk.CTkFrame(content_frame, fg_color=BG_COLOR)
left_panel.grid_columnconfigure(0, weight=1)
left_panel.grid_rowconfigure(0, weight=1)

guide_box = ctk.CTkFrame(left_panel, fg_color=BOX_COLOR, corner_radius=30)
guide_image_label = ctk.CTkLabel(guide_box, text="")
guide_image_label.pack(expand=True)

select_btn = ctk.CTkButton(left_panel, text="Select image", fg_color=BUTTON_LEFT,
                           text_color="black", command=select_image)

export_btn = ctk.CTkButton(left_panel, text="Export", fg_color=BUTTON_LEFT,
                           text_color="black", command=export_image)

# CENTER
center_panel = ctk.CTkFrame(content_frame, fg_color=BG_COLOR)
center_panel.grid_columnconfigure(0, weight=1)
center_panel.grid_rowconfigure(0, weight=1)

image_box = ctk.CTkFrame(center_panel, fg_color=BOX_COLOR, corner_radius=40)
center_image_label = ctk.CTkLabel(image_box, text="Edited image will appear here")
center_image_label.pack(expand=True)

# RIGHT
right_panel = ctk.CTkFrame(content_frame, fg_color=BG_COLOR)
right_panel.grid_columnconfigure(0, weight=1)

remove_btn = ctk.CTkButton(right_panel, text="Object removal tool",
                           fg_color=BUTTON_RIGHT, text_color="black")

denoise_btn = ctk.CTkButton(
    right_panel,
    text="Image denoising",
    fg_color=BUTTON_RIGHT,
    text_color="black",
    command=toggle_denoise_controls
)

bg_remove_btn = ctk.CTkButton(right_panel, text="Remove background",
                              fg_color=BUTTON_RIGHT, text_color="black",
                              command=remove_background_action)

flip_h_btn = ctk.CTkButton(right_panel, text="Flip horizontal",
                           fg_color=BUTTON_RIGHT, text_color="black",
                           command=flip_horizontal_action)

flip_v_btn = ctk.CTkButton(right_panel, text="Flip vertical",
                           fg_color=BUTTON_RIGHT, text_color="black",
                           command=flip_vertical_action)

# ----- Denoise Advanced Options Frame (hidden by default) -----
denoise_controls_frame = ctk.CTkFrame(right_panel, fg_color=BG_COLOR)
denoise_controls_frame.grid_columnconfigure(0, weight=1)

denoise_title = ctk.CTkLabel(denoise_controls_frame, text="Advanced Options",
                             font=("Georgia", 18, "bold"), text_color=TEXT_COLOR)

denoise_auto_btn = ctk.CTkButton(
    denoise_controls_frame,
    text="Auto Denoise",
    fg_color=BUTTON_RIGHT,
    text_color="black",
    command=denoise_auto_action
)

denoise_strength_label = ctk.CTkLabel(denoise_controls_frame, text="Strength",
                                      font=("Georgia", 14, "bold"), text_color=TEXT_COLOR)

denoise_strength_value = ctk.CTkLabel(denoise_controls_frame, text="10",
                                      font=("Arial", 12), text_color=TEXT_COLOR)

denoise_strength_slider = ctk.CTkSlider(
    denoise_controls_frame,
    from_=1,
    to=30,
    number_of_steps=29,
    command=schedule_manual_denoise_update
)
denoise_strength_slider.set(10)

edge_preserving_var = ctk.IntVar(value=1)
salt_pepper_var = ctk.IntVar(value=0)

edge_preserving_switch = ctk.CTkSwitch(
    denoise_controls_frame,
    text="Edge-Preserving (Bilateral)",
    variable=edge_preserving_var,
    onvalue=1,
    offvalue=0,
    command=schedule_manual_denoise_update
)

salt_pepper_switch = ctk.CTkSwitch(
    denoise_controls_frame,
    text="Salt & Pepper Fix (Median)",
    variable=salt_pepper_var,
    onvalue=1,
    offvalue=0,
    command=schedule_manual_denoise_update
)

denoise_title.grid(row=0, column=0, sticky="w", pady=(0, 6))
denoise_auto_btn.grid(row=1, column=0, sticky="ew", pady=(0, 10))

strength_row = ctk.CTkFrame(denoise_controls_frame, fg_color=BG_COLOR)
strength_row.grid_columnconfigure(0, weight=1)
strength_row.grid(row=2, column=0, sticky="ew", pady=(0, 4))

denoise_strength_label.grid(in_=strength_row, row=0, column=0, sticky="w")
denoise_strength_value.grid(in_=strength_row, row=0, column=1, sticky="e")

denoise_strength_slider.grid(row=3, column=0, sticky="ew", pady=(0, 10))
edge_preserving_switch.grid(row=4, column=0, sticky="w", pady=(0, 6))
salt_pepper_switch.grid(row=5, column=0, sticky="w")

denoise_controls_frame.grid_remove()

# Existing sliders/labels on right (kept)
low_label = ctk.CTkLabel(right_panel, text="Low light enhancement",
                         font=("Georgia", 20, "bold"))
low_slider = ctk.CTkSlider(right_panel)

tone_label = ctk.CTkLabel(right_panel, text="Artistic color tone",
                          font=("Georgia", 20, "bold"))
tone_slider = ctk.CTkSlider(right_panel)

preset_menu = ctk.CTkOptionMenu(right_panel,
                                values=["Preset 1", "Preset 2", "Preset 3", "Preset 4"],
                                fg_color=BUTTON_RIGHT, text_color="black")

# NEW Reset button moved to bottom, separated
reset_btn = ctk.CTkButton(
    right_panel,
    text="Reset",
    fg_color=BUTTON_RIGHT,
    text_color="black",
    command=reset_image_action
)

# -----------------------------------------------------------
# GRID
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
# denoise_controls_frame appears under denoise_btn when toggled (row=2)
bg_remove_btn.grid(row=3, column=0, sticky="ew", pady=5)
flip_h_btn.grid(row=4, column=0, sticky="ew", pady=5)
flip_v_btn.grid(row=5, column=0, sticky="ew", pady=5)

low_label.grid(row=6, column=0, sticky="w")
low_slider.grid(row=7, column=0, sticky="ew", pady=5)
tone_label.grid(row=8, column=0, sticky="w")
tone_slider.grid(row=9, column=0, sticky="ew", pady=5)
preset_menu.grid(row=10, column=0, sticky="e", pady=5)

# Reset is now at the bottom, separated with extra padding
reset_btn.grid(row=11, column=0, sticky="ew", pady=(25, 5))


# -----------------------------------------------------------
# RESIZING LOGIC (NO GLITCHES)
# -----------------------------------------------------------
def resize_ui():
    """Recalculates font sizes and button heights instantly."""
    w = app.winfo_width()
    h = app.winfo_height()
    
    # Calculate scale (base 1600x900)
    scale = min(w / 1600, h / 900)
    scale = max(0.5, min(1.5, scale)) # Clamp scale

    # Update Standard Labels
    scaled_font_bold = ("Georgia", int(20 * scale), "bold")
    
    title_label.configure(font=("Georgia", int(32 * scale), "bold"))
    low_label.configure(font=scaled_font_bold)
    tone_label.configure(font=scaled_font_bold)

    # Update Buttons
    btn_height = int(45 * scale)
    btn_radius = int(30 * scale)
    btn_font = ("Arial", int(16 * scale))

    for btn in [
        select_btn, export_btn, remove_btn, denoise_btn, denoise_auto_btn,
        bg_remove_btn, flip_h_btn, flip_v_btn, reset_btn
    ]:
        btn.configure(height=btn_height, corner_radius=btn_radius, font=btn_font)

    # Update Denoise UI
    denoise_title.configure(font=("Georgia", int(18 * scale), "bold"))
    denoise_strength_label.configure(font=("Georgia", int(14 * scale), "bold"))
    denoise_strength_value.configure(font=("Arial", int(12 * scale)))
    edge_preserving_switch.configure(font=("Arial", int(14 * scale)))
    salt_pepper_switch.configure(font=("Arial", int(14 * scale)))

    # Redraw images immediately
    display_image_in_guidebox()
    display_image_in_centerbox()


def on_resize(event):
    """
    Called whenever the window changes. 
    """
    global last_width, last_height

    # --- 1. SAFETY CHECK (LAZY INIT) ---
    # If last_width/height haven't been defined yet, define them now.
    if 'last_width' not in globals():
        last_width = 1600
        last_height = 900

    curr_w = app.winfo_width()
    curr_h = app.winfo_height()

    # --- 2. CHECK: Did the size actually change? --- 
    if curr_w == last_width and curr_h == last_height:
        return

    # 3. Update stored size
    last_width = curr_w
    last_height = curr_h

    # 4. EXECUTE IMMEDIATELY
    resize_ui()

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
image_box.bind("<Configure>", lambda e: display_image_in_centerbox())

# -----------------------------------------------------------
app.mainloop()
