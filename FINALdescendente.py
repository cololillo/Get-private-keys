import os
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import requests
import requests_cache

# Habilita el almacenamiento en caché
requests_cache.install_cache('http_cache', backend='sqlite', expire_after=3600)  # Almacena en caché durante 1 hora

def make_cached_request(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Solicitud realizada directamente desde el servidor")
        elif response.from_cache:
            print("Solicitud obtenida desde la caché")
        return response.json()  # Procesa la respuesta exitosa
    except requests.RequestException as e:
        print(f"Error en la solicitud: {str(e)}")
        return None

# Ejemplo de uso
url = 'https://api.example.com/data'

# Realiza la primera solicitud
data = make_cached_request(url)
print(data)

# Realiza la misma solicitud nuevamente
data = make_cached_request(url)
print(data)
# Función para buscar direcciones de Bitcoin en una página específica
def buscar_direcciones_pagina(url, target_addresses):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    td_tags = soup.find_all('td')

    for td in td_tags:
        matches = re.findall(bitcoin_address_pattern, td.get_text())
        for match in matches:
            if match in target_addresses:
                return match, url  # Devuelve la dirección encontrada y la URL de la página
    return None, None

# Función para verificar el saldo de una dirección de Bitcoin usando la API de Esplora de Blockstream
def verificar_saldo_direccion(address):
    try:
        url = f'https://blockstream.info/api/address/{address}/utxo'
        response = requests.get(url)
        if response.status_code == 200:
            utxos = response.json()
            total_balance = sum([utxo['value'] for utxo in utxos])
            return total_balance / 100000000  # Convertir el saldo de satoshis a BTC
        else:
            print(f"No se pudo obtener el saldo para la dirección: {address}")
            return None
    except Exception as e:
        print(f"Error al verificar saldo para la dirección {address}: {str(e)}")
        return None

# Función para guardar los datos encontrados en un archivo JSON
def guardar_datos(billetera, saldo, pagina):
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    folder_path = os.path.join(os.path.expanduser('~'), 'Documents', 'Claves Btc')
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'Claves Btc')
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    if not os.path.exists(desktop_path):
        os.makedirs(desktop_path)
    
    file_name = f'bitcoin_data_{timestamp}.json'
    file_path = os.path.join(folder_path, file_name)
    desktop_file_path = os.path.join(desktop_path, file_name)

    data = {
        'Billetera': billetera,
        'Saldo BTC': saldo,
        'Pagina': pagina
    }

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    
    with open(desktop_file_path, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"Datos guardados en {file_path} y {desktop_file_path}")

# Búsqueda en múltiples páginas de la última a la primera
def buscar_en_multiples_paginas(base_url, target_addresses, start_page, end_page):
    # Asegurarse de que start_page sea mayor o igual que end_page para la búsqueda descendente
    if start_page < end_page:
        start_page, end_page = end_page, start_page

    page_number = start_page
    while page_number >= end_page:
        page_url = f'{base_url}{page_number}'
        found_address, found_page = buscar_direcciones_pagina(page_url, target_addresses)
        if found_address:
            print(f"Dirección de Bitcoin encontrada en la página {page_number}: {found_address}")
            balance = verificar_saldo_direccion(found_address)
            if balance is not None:
                print(f"Saldo de la dirección {found_address}: {balance} BTC")
                guardar_datos(found_address, balance, found_page)
            return
        else:
            print(f"No se encontró en la página {page_number}")
            page_number -= 1

    print("Llegaste a la última página especificada sin encontrar la dirección.")

# URL base de la página que contiene las direcciones de Bitcoin
base_url = 'https://privatekeys.pw/keys/bitcoin/'

# Lista de direcciones específicas que quieres buscar
target_addresses = [
    "13zb1hQbWVsc2S7ZTZnP2G4undNNpdh5so",  
    "1BY8GQbnueYofwSuFAT3USAhGjPrkxDdW9",
    "1MVDYgVaSN6iKKEsbzRUAYFrYJadLYZvvZ",
    "19vkiEajfhuZ8bs8Zu2jgmC6oqZbWqhxhG",  
]

# Patrón de búsqueda para las direcciones de Bitcoin
bitcoin_address_pattern = re.compile(r'([13][a-km-zA-HJ-NP-Z1-9]{25,34})')

# Ejemplo de llamada a buscar_en_multiples_paginas especificando start_page y end_page
buscar_en_multiples_paginas(
    base_url,
    target_addresses,
    start_page=3220063686963387736,
    end_page=1949680480282643006
)
