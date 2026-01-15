import cv2
import numpy as np

# Funcția 1: Metoda NLM (Curățare intensă)
def denoise_nlm(image, strength):
    return cv2.fastNlMeansDenoisingColored(image, None, h=strength, hColor=strength, templateWindowSize=7, searchWindowSize=21)

# Funcția 2: Metoda Bilateral (Păstrare margini - Default)
def denoise_bilateral(image, strength):
    # d trebuie să fie un număr întreg
    d = int(strength)
    return cv2.bilateralFilter(image, d, sigmaColor=75, sigmaSpace=75)



# --- FUNCȚIILE TALE ---

def denoise_nlm(image, strength):
    # h=strength; cu cât e mai mare, cu atât elimină mai mult zgomot
    return cv2.fastNlMeansDenoisingColored(image, None, h=strength, hColor=strength, templateWindowSize=7, searchWindowSize=21)

def denoise_bilateral(image, strength):
    # d=strength; diametrul zonei de filtrare
    d = int(strength)
    return cv2.bilateralFilter(image, d, sigmaColor=75, sigmaSpace=75)

# --- CODUL DE TESTARE ---

# Folosește calea relativă pe care am discutat-o
cale_imagine = '../image_testing/Kodim17_noisy.jpg'
imagine_originala = cv2.imread(cale_imagine)

# Verificăm dacă imaginea s-a încărcat corect
if imagine_originala is None:
    # Mesaj de eroare în engleză
    print(f"Error: Could not find the file at {cale_imagine}. Please check the file name and path!")
else:
    # Mesaj de confirmare în engleză
    print("Image loaded successfully. Processing... please wait.")
    
    # 2. Aplicăm funcțiile (folosim o putere de 15 pentru test vizibil)
    rezultat_bilateral = denoise_bilateral(imagine_originala, 15) # Metoda Edge-preserving
    rezultat_nlm = denoise_nlm(imagine_originala, 10)             # Metoda Deep clean

    # 3. Afișăm rezultatele în ferestre separate
    # Titlurile ferestrelor sunt de obicei în engleză în aplicațiile software
    cv2.imshow('Original Image - Press any key to close', imagine_originala)
    cv2.imshow('Bilateral Filter (Edge Preserving)', rezultat_bilateral)
    cv2.imshow('Non-Local Means (Deep Clean)', rezultat_nlm)

    # Mesaj final în terminal
    print("Process completed. Windows are open. Press any key on an image window to exit.")

    # 4. Comandă pentru a menține ferestrele deschise până apeși o tastă
    cv2.waitKey(0)
    cv2.destroyAllWindows()