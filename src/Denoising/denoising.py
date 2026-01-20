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

