import cv2
import numpy as np

# ==========================================================
# SECȚIUNEA 1: LOGICA DE PROCESARE (Clasa principală)
# ==========================================================
class ImageDenoiser:
    @staticmethod
    def estimate_noise_level(image: np.ndarray) -> float:
        if len(image.shape) > 2:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    def get_auto_params(self, image: np.ndarray):
        """Analizează imaginea și returnează parametrii optimi."""
        noise_val = self.estimate_noise_level(image)
        
        # Detectare Salt & Pepper
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) > 2 else image
        sp_ratio = (np.sum(gray <= 2) + np.sum(gray >= 253)) / gray.size
        needs_sp_fix = sp_ratio > 0.005 

        if noise_val < 150:
            return 5, True, needs_sp_fix
        elif noise_val < 600:
            return 10, True, needs_sp_fix
        else:
            return 12, False, needs_sp_fix
        
    @staticmethod
    def denoise_nlm(image, strength):
        h = max(1, strength)
        if len(image.shape) > 2:
            return cv2.fastNlMeansDenoisingColored(image, None, h, h, 7, 21)
        return cv2.fastNlMeansDenoising(image, None, h, 7, 21)

    @staticmethod
    def denoise_bilateral(image, strength):
        d = int(strength / 2) + 1
        s_color = strength * 5
        return cv2.bilateralFilter(image, d, s_color, 75)

# ==========================================================
# SECȚIUNEA 2: ENTRY POINT PENTRU OPTIUNI AVANSATE (SLIDERS)
# ==========================================================
def apply_denoising_logic(image: np.ndarray, strength: int, edge_preserving: bool, salt_pepper_fix: bool) -> np.ndarray:
    """Această funcție va fi apelată de sliderele din 'Advanced Options'."""
    denoiser = ImageDenoiser()
    if image is None: return None

    if edge_preserving:
        result = denoiser.denoise_bilateral(image, strength)
    else:
        result = denoiser.denoise_nlm(image, strength)

    if salt_pepper_fix:
        result = cv2.medianBlur(result, 5 if strength > 10 else 3)

    return result

# ==========================================================
# SECȚIUNEA 2 B: ENTRY POINT PENTRU BUTONUL AUTO
# ==========================================================
def apply_auto_denoising_logic(image: np.ndarray):
    """
    Această funcție returnează și parametrii, nu doar imaginea.
    Folositoare pentru ca GUI-ul să actualizeze slider-ele automat.
    """
    denoiser = ImageDenoiser()
    if image is None: return None, 0, True, False

    # Calculăm valorile
    strength, edge_preserving, salt_pepper_fix = denoiser.get_auto_params(image)
    
    # Procesăm imaginea cu aceste valori
    result = apply_denoising_logic(image, strength, edge_preserving, salt_pepper_fix)

    # Returnăm tot pachetul către colegii de la GUI
    return result, strength, edge_preserving, salt_pepper_fix



# ==========================================================
# SECȚIUNEA 3: CONSOLA DE TESTARE INTERACTIVĂ 
# ==========================================================
denoiser_instance = ImageDenoiser() # Instanța unică a denoiser-ului
original_image = None # Variabila globală pentru imaginea originală
is_updating = False  # Variabilă globală pentru a preveni bucla infinită
def update_display(x=None):
    global is_updating
    if original_image is None or is_updating:
        return

    # Citim valorile curente
    strength = cv2.getTrackbarPos('Strength', 'Denoising Test Console')
    mode = cv2.getTrackbarPos('Mode (0:NLM, 1:Bilat)', 'Denoising Test Console')
    sp_fix = cv2.getTrackbarPos('Salt&Pepper (0:OFF, 1:ON)', 'Denoising Test Console')
    auto_trigger = cv2.getTrackbarPos('AUTO-SUGGEST (0/1)', 'Denoising Test Console')

    if auto_trigger == 1:
        print("\n--- AUTO-SUGGEST ACTIVAT ---")
        is_updating = True # Blocăm apelurile noi
        
        # Calculăm parametrii auto
        _, s_auto, m_auto, sp_auto = apply_auto_denoising_logic(original_image)
        
        # Actualizăm pozițiile sliderelor (acestea ar declanșa update_display normal)
        cv2.setTrackbarPos('Strength', 'Denoising Test Console', s_auto)
        cv2.setTrackbarPos('Mode (0:NLM, 1:Bilat)', 'Denoising Test Console', 1 if m_auto else 0)
        cv2.setTrackbarPos('Salt&Pepper (0:OFF, 1:ON)', 'Denoising Test Console', 1 if sp_auto else 0)
        cv2.setTrackbarPos('AUTO-SUGGEST (0/1)', 'Denoising Test Console', 0)
        
        is_updating = False # Deblocăm
        
        # Forțăm o singură procesare finală cu noile valori
        processed_image = apply_denoising_logic(original_image, s_auto, m_auto, sp_auto)
        cv2.imshow('Denoising Test Console', processed_image)
        return

    # Procesare normală (manuală)
    processed_image = apply_denoising_logic(
        original_image, 
        max(1, strength), 
        mode == 1, 
        sp_fix == 1
    )
    cv2.imshow('Denoising Test Console', processed_image)
# if __name__ == "__main__":
#     cale_absoluta = "/Users/ioana/Library/CloudStorage/OneDrive-Personal/School-DESKTOP-5LL07UF/Erasmus/ESAT/proiect/image_testing/noisy.png"
    
#     print(f"Încărcare imagine de la: {cale_absoluta}...")
#     original_image = cv2.imread(cale_absoluta) # Folosim original_image aici

#     if original_image is None:
#         print("EROARE: Imaginea nu a fost găsită la calea specificată.")
#     else:
#         print("Succes! Consola de testare este activă.")
        
#         cv2.namedWindow('Denoising Test Console')
#         cv2.namedWindow('Original Image') # Fereastră pentru imaginea originală

#         # Creare Slidere
#         cv2.createTrackbar('Strength', 'Denoising Test Console', 10, 30, update_display)
#         cv2.createTrackbar('Mode (0:NLM, 1:Bilat)', 'Denoising Test Console', 1, 1, update_display)
#         cv2.createTrackbar('Salt&Pepper (0:OFF, 1:ON)', 'Denoising Test Console', 0, 1, update_display)
        
#         # Slider special pentru declanșarea funcției AUTO-SUGGEST
#         cv2.createTrackbar('AUTO-SUGGEST (0/1)', 'Denoising Test Console', 0, 1, update_display)

#         # Afișare inițială
#         update_display()
        
#         print("\n--- CONSOLĂ DE TESTARE INTERACTIVĂ ---")
#         print("Reglează setările cu sliderele.")
#         print("Activează 'AUTO-SUGGEST' pentru a vedea recomandările algoritmului.")
#         print("Apasă orice tastă pentru a închide ferestrele.")
        
#         cv2.waitKey(0)
#         cv2.destroyAllWindows()
