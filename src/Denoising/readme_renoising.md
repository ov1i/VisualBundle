# Denoising Module Documentation

This module contains the logic for image denoising. It is designed to be integrated into the main GUI with two options: **Automatic** and **Manual (Advanced)**.

### 1. The "Automatic" Option
When the user clicks the "Auto" button, you should call:
`result, strength, mode, sp_fix = apply_auto_denoising_logic(image)`

* **Action**: The function analyzes the noise and returns the processed image plus the best settings found.
* **GUI Update**: You can use the returned `strength`, `mode`, and `sp_fix` to move your sliders and toggles to the correct positions automatically.

### 2. The "Advanced" Option (Manual Sliders)
When the user adjusts sliders manually, you should call:
`result = apply_denoising_logic(image, strength, edge_preserving, salt_pepper_fix)`

### 3. Parameters for the GUI
To build the "Advanced Options" menu, you need these inputs:

* **Strength** (Slider): Integer values from **1 to 30**.
* **Edge-Preserving** (Toggle/Switch): 
    * **True**: Uses Bilateral Filter (keeps details sharp).
    * **False**: Uses NLM Filter (stronger cleaning).
* **Salt & Pepper Fix** (Toggle/Switch): 
    * **True**: Activates Median Filter to remove black/white dots.
    * **False**: Filter is OFF.
 
IMPORTANT : The last part called " SECTIUNEA 3: CONSOLA DE TESTARE INTERACTIVA" is only for testing and should be removed in the final version. 
