from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import time
import csv

# Configuración del navegador
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
# chrome_options.add_argument('--headless')  # Opcional: modo sin ventana

# Iniciar el navegador
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def extract_name():
    try:
        return WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//h1[@class="DUwDvf lfPIob"]'))
        ).text
    except TimeoutException:
        return "Nombre no disponible"

def extract_phone():
    try:
        phone_button = driver.find_element(By.XPATH, '//button[contains(@data-item-id, "phone")]')
        return phone_button.find_element(By.XPATH, './/div[2]').text
    except NoSuchElementException:
        return "N/A"

try:
    # Abrir Google Maps
    driver.get("https://www.google.com/maps ")
    time.sleep(5)

    # Buscar término
    search_box = driver.find_element(By.ID, "searchboxinput")
    search_box.clear()
    search_box.send_keys("Gimnasio")

    # Hacer clic en el botón de búsqueda
    search_button = driver.find_element(By.XPATH, '//button[@aria-label="Buscar"]')
    search_button.click()

    time.sleep(5)

    # Localizar el contenedor de resultados
    results_panel = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]'))
    )

    print("Cargando todos los resultados...")

    # ========== SCROLL TOTAL HACIA ABAJO PARA CARGAR TODOS LOS RESULTADOS ==========
    previous_count = 0
    MAX_RETRIES = 10
    retry = 0

    while retry < MAX_RETRIES:
        driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', results_panel)
        time.sleep(3)
        current_links = driver.find_elements(By.XPATH, '//a[@class="hfpxzc"]')
        if len(current_links) == previous_count:
            print("No hay más resultados nuevos.")
            break
        previous_count = len(current_links)
        retry += 1

    print(f"Total de resultados encontrados: {previous_count}")

    # ========== VOLVER AL INICIO DEL PANEL DE RESULTADOS ==========
    print("Volviendo al inicio del panel...")
    driver.execute_script('arguments[0].scrollTop = 0', results_panel)
    time.sleep(2)

    extracted_data = []

    # ========== PROCESAR CADA LUGAR UNO POR UNO, SIN SALTEAR ==========
    for i in range(previous_count):
        try:
            # Re-localizar los elementos cada vez (para evitar referencias obsoletas)
            links = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//a[@class="hfpxzc"]'))
            )

            # Verificar si el índice existe
            if i >= len(links):
                print(f"Índice {i} fuera de rango. Saltando...")
                continue

            link = links[i]

            # Hacer clic en el elemento actual
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", link)
            time.sleep(1)
            link.click()
            time.sleep(3)

            name = extract_name()
            phone = extract_phone()

            print(f"{i + 1}. Nombre: {name} | Teléfono: {phone}")
            extracted_data.append({
                "Nombre": name,
                "Teléfono": phone
            })

        except Exception as e:
            print(f"No se pudo procesar el lugar {i + 1}: {str(e)}")

    # ========== GUARDAR EN CSV ==========
    with open('resultados_estudio_juridico.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["Nombre", "Teléfono"])
        writer.writeheader()
        writer.writerows(extracted_data)

finally:
    driver.quit()