# test_sheets.py (Versión con ID)

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Importar solo las credenciales desde tu archivo config.py
try:
    from config import GOOGLE_CREDS
except ImportError:
    print("❌ Error: No se pudo encontrar el archivo 'config.py'.")
    exit()

# --- MODIFICACIÓN IMPORTANTE ---
# Pega aquí el ID que copiaste de la URL de tu Google Sheet
SPREADSHEET_ID = "12IscHUDMLFbnbujRakVMEAwc_jk5yHU9B5EfqGyFZ2g"
SHEET_TAB_NAME = "RegistroMXN" # El nombre de la pestaña sigue siendo necesario

# Definir los permisos (scopes)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]

print("--- Iniciando prueba de escritura en Google Sheets ---")

try:
    # 1. Autenticación
    print("1. Autenticando...")
    creds = Credentials.from_service_account_info(GOOGLE_CREDS, scopes=SCOPES)
    client = gspread.authorize(creds)
    print("   ... Autenticación exitosa.")

    # 2. Abrir el ARCHIVO usando su ID
    print(f"2. Abriendo el ARCHIVO por su ID: {SPREADSHEET_ID}...")
    spreadsheet = client.open_by_key(SPREADSHEET_ID) # <-- Usando el método open_by_key()
    print("   ... Archivo abierto correctamente.")

    # 3. Seleccionar la HOJA (pestaña)
    print(f"3. Seleccionando la HOJA '{SHEET_TAB_NAME}'...")
    sheet = spreadsheet.worksheet(SHEET_TAB_NAME)
    print("   ... Hoja seleccionada correctamente.")

    # 4. Preparar fila de prueba
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_row = [timestamp, "Prueba con ID", 500.0, 25.0, 20.0]
    print(f"4. Preparando para añadir la fila: {test_row}")

    # 5. Añadir la fila
    sheet.append_row(test_row)
    print("5. ¡Fila añadida!")

    # 6. Mensaje de éxito
    print("\n✅ ¡Éxito! La fila se ha añadido correctamente a tu Google Sheet.")

except gspread.exceptions.WorksheetNotFound:
    print(f"\n❌ Error: Se abrió el archivo, pero no se encontró la HOJA (pestaña) llamada '{SHEET_TAB_NAME}'.")
except Exception as e:
    print(f"\n❌ Error: No se pudo escribir en la hoja. Detalles del error:")
    print(repr(e))

print("\n--- Prueba finalizada ---")