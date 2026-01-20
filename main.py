""" MAIN -> this is the entry point of the app """
# import cv2
# import numpy
# from src.Llie import enhance_image

# img = cv2.imread('res/city.png')
# enhanced_image = enhance_image(img)
# cv2.imwrite('res/test.png', enhanced_image)


import sys
import os
import cv2
import numpy as np

# --- 1. ROBUST PATH SETUP ---
# Get the absolute path of the directory containing THIS script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define potential build locations relative to the script
# We look in the current folder, up one level, and up two levels
possible_paths = [
    os.path.join(script_dir, '.build'),           # If script is in root
    os.path.join(script_dir, 'build'),            # Standard build name
    os.path.join(script_dir, '../.build'),        # If script is in gui/ or scripts/
    os.path.join(script_dir, '../build'),
    os.path.join(script_dir, '../../.build'),     # Deeply nested
]

module_path = None
for path in possible_paths:
    # Check if the specific .so file exists in this path (partial match for safety)
    if os.path.exists(path):
        for file in os.listdir(path):
            if file.startswith("ObjectRemover_core") and file.endswith(".so"):
                module_path = path
                break
    if module_path:
        break

if module_path:
    sys.path.append(module_path)
    print(f"✅ Found library at: {module_path}")
else:
    print("❌ Critical Error: compiled library (ObjectRemover_core.so) not found in .build or build folders.")
    print(f"   Searched in: {possible_paths}")
    sys.exit(1)

import ObjectRemover_core
# ------------------------------------------------
# --- 2. UI LOGIC ---

# Global State
drawing = False
ix, iy = -1, -1
roi_rect = None # (x, y, w, h)
img_display = None

def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, img_display, roi_rect

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            img_copy = img_display.copy()
            cv2.rectangle(img_copy, (ix, iy), (x, y), (0, 0, 255), 2)
            cv2.imshow("Object Remover", img_copy)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        # Calculate standard x,y,w,h regardless of drag direction
        x_start = min(ix, x)
        y_start = min(iy, y)
        w = abs(ix - x)
        h = abs(iy - y)
        roi_rect = (x_start, y_start, w, h)
        
        # Draw final box
        cv2.rectangle(img_display, (x_start, y_start), (x_start + w, y_start + h), (0, 0, 255), 2)
        cv2.imshow("Object Remover", img_display)
        
        print(f"Selection: x={x_start}, y={y_start}, w={w}, h={h}")

def main():
    # --- CRITICAL FIX: Tell main to use the global variables ---
    global img_display, roi_rect 
    
    # 1. Load Image
    image_path = "input.jpg"
    if len(sys.argv) > 1:
        image_path = sys.argv[1]

    if not os.path.exists(image_path):
        print(f"'{image_path}' not found. Creating a test image...")
        dummy = np.zeros((400, 400, 3), dtype=np.uint8)
        dummy[:] = (100, 100, 100) 
        cv2.circle(dummy, (200, 200), 50, (255, 0, 0), -1)
        cv2.imwrite("res/input.jpg", dummy)
        image_path = "res/input.jpg"

    original_img = cv2.imread(image_path)
    img_display = original_img.copy()

    # 2. Initialize C++ Engine
    try:
        remover = ObjectRemover_core.PatchRemover()
        print("Generated C++ Instance. Sending Image to Memory...")
        remover.set_image(original_img)
    except Exception as e:
        print(f"❌ Error initializing C++ core: {e}")
        return

    # 3. Setup Window
    cv2.namedWindow("Object Remover")
    cv2.setMouseCallback("Object Remover", draw_rectangle)
    
    print("\n--- CONTROLS ---")
    print(" [Mouse] : Click and drag to select object")
    print(" [SPACE] : Run Removal (Process)")
    print(" [R]     : Reset Image")
    print(" [Q]     : Quit")

    while True:
        cv2.imshow("Object Remover", img_display)
        key = cv2.waitKey(1) & 0xFF

        # --- PROCESS ---
        if key == 32: # SPACE bar
            # Now 'roi_rect' correctly refers to the global one set by the mouse
            if roi_rect and roi_rect[2] > 0 and roi_rect[3] > 0:
                print("⚡ Processing in C++...")
                
                remover.set_selection(*roi_rect)
                
                try:
                    remover.process()
                    result_img = remover.get_result()
                    
                    combined = np.hstack((original_img, result_img))
                    cv2.imshow("Result (Left: Original, Right: Cleaned)", combined)
                    print("✅ Done! Result retrieved.")
                    
                except RuntimeError as e:
                    print(f"❌ C++ Error: {e}")
            else:
                print("⚠️ Please select an area first.")

        # --- RESET ---
        elif key == ord('r'):
            img_display = original_img.copy()
            roi_rect = None  # This write caused the error before!
            remover.set_image(original_img)
            try:
                cv2.destroyWindow("Result (Left: Original, Right: Cleaned)")
            except:
                pass
            print("🔄 Reset.")

        # --- QUIT ---
        elif key == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
