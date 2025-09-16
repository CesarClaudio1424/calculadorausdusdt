import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import dropbox

# --- Importar credenciales y tokens ---
try:
    from config import GOOGLE_CREDS, SPREADSHEET_ID, SHEET_TAB_NAME, DROPBOX_ACCESS_TOKEN
except ImportError:
    # No hacer nada si no existe, se asumirá que estamos en la nube
    pass

# --- FUNCIONES DE CONEXIÓN ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]

@st.cache_resource
def connect_to_google_sheets():
    try:
        creds_dict = st.secrets["google_creds"]
    except (FileNotFoundError, KeyError):
        creds_dict = GOOGLE_CREDS
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_resource
def connect_to_dropbox():
    """Conecta a Dropbox usando el token."""
    try:
        token = st.secrets["DROPBOX_ACCESS_TOKEN"]
    except (FileNotFoundError, KeyError):
        token = DROPBOX_ACCESS_TOKEN
    return dropbox.Dropbox(token)

@st.cache_data(ttl=60)
def get_client_data(_gsheet_client):
    try:
        spreadsheet_id = st.secrets.get("SPREADSHEET_ID", SPREADSHEET_ID)
        spreadsheet = _gsheet_client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet("Clientes")
        data = worksheet.get_all_records()
        if not data: return pd.DataFrame(columns=['Alias Cliente', 'Saldo USDT', 'Saldo MXN'])
            
        df = pd.DataFrame(data)
        df['Saldo USDT'] = df['Saldo USDT'].astype(str).str.replace(r'[$,]', '', regex=True)
        df['Saldo MXN'] = df['Saldo MXN'].astype(str).str.replace(r'[$,]', '', regex=True)
        df['Saldo USDT'] = pd.to_numeric(df['Saldo USDT'], errors='coerce').fillna(0)
        df['Saldo MXN'] = pd.to_numeric(df['Saldo MXN'], errors='coerce').fillna(0)
        return df
    except gspread.exceptions.WorksheetNotFound:
        st.error("Error: No se encontró la hoja 'Clientes' en tu Google Sheet.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"No se pudo cargar la lista de clientes: {e}")
        return pd.DataFrame()

def upload_to_dropbox(dbx_client, file_object, client_name):
    """Sube un archivo a Dropbox y devuelve el link para compartir."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dropbox_path = f"/{client_name.replace(' ', '_')}/{timestamp}_{file_object.name}"
        
        dbx_client.files_upload(file_object.getvalue(), dropbox_path, mode=dropbox.files.WriteMode('overwrite'))
        
        try:
            links = dbx_client.sharing_list_shared_links(path=dropbox_path).links
            link = links[0].url if links else None
        except dropbox.exceptions.ApiError:
            link = None

        if link is None:
            link_metadata = dbx_client.sharing_create_shared_link_with_settings(dropbox_path)
            link = link_metadata.url
        
        return link.replace("?dl=0", "?raw=1")
    except Exception as e:
        st.warning(f"No se pudo subir el archivo a Dropbox: {e}")
        return ""

# --- FUNCIONES DE LA INTERFAZ ---

def create_calculation_row(row_index, precio_compra, precio_venta, mode_vende, mode_compra):
    div_height = 78 if row_index == 0 else 38
    col_vende, _, col_compra = st.columns([1, 0.2, 1])
    if row_index == 0:
        with col_vende: st.subheader("Cliente Vende / Yo Compro")
        with col_compra: st.subheader("Cliente Compra / Yo Vendo")

    with col_vende:
        # ... (Lógica de cálculo sin cambios)
        st.file_uploader("Comprobante", type=["png", "jpg", "jpeg"], key=f"uploader_vende_{row_index}", label_visibility="collapsed")

    with col_compra:
        # ... (Lógica de cálculo sin cambios)
        st.file_uploader("Comprobante", type=["png", "jpg", "jpeg"], key=f"uploader_compra_{row_index}", label_visibility="collapsed")
    
    return {"pesos_pagar": pesos_a_pagar, "usdt_recibir": usdt_a_recibir, "pesos_cobrar": pesos_a_cobrar, "usdt_entregar": usdt_a_entregar}

def create_ajuste_row(row_index):
    # ... (Lógica de ajuste sin cambios, añadiendo file uploaders)
    st.file_uploader("Comprobante de Pago", type=["png", "jpg", "jpeg"], key=f"uploader_pago_{row_index}", label_visibility="collapsed")
    st.file_uploader("Comprobante de Recibo", type=["png", "jpg", "jpeg"], key=f"uploader_recibo_{row_index}", label_visibility="collapsed")
    
    return {"pago_monto": pago_monto, "pago_moneda": pago_moneda, "recibo_monto": recibo_monto, "recibo_moneda": recibo_moneda}

def main():
    st.set_page_config(page_title="Calculadora y Registro", page_icon="🏦", layout="wide")
    st.markdown("<h1 style='text-align: center;'>Calculadora y Registro de Operaciones 🏦</h1>", unsafe_allow_html=True)
    st.markdown("---")

    gsheet_client = connect_to_google_sheets()
    dbx_client = connect_to_dropbox()
    
    # ... (Callbacks y resto de la app sin cambios hasta el botón de guardar)

    # --- 5. REGISTRAR OPERACIONES ---
    st.header("5. Registrar Operaciones")
    col_save, col_clear_all = st.columns([3,1])
    with col_save:
        if st.button("💾 Guardar y Actualizar Saldo", use_container_width=True, type="primary"):
            if not selected_client_name or selected_client_name == "-- Seleccione un Cliente --":
                st.error("Por favor, seleccione un cliente antes de guardar.")
            else:
                data_to_save_batch = []
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                with st.spinner(f"Procesando y guardando operaciones..."):
                    # Procesar filas de cálculo
                    for i, row_data in enumerate(all_rows_data):
                        if row_data["pesos_pagar"] > 0 or row_data["usdt_recibir"] > 0:
                            link_compra = ""
                            uploader_key = f"uploader_vende_{i}"
                            if uploader_key in st.session_state and st.session_state[uploader_key] is not None:
                                link_compra = upload_to_dropbox(dbx_client, st.session_state[uploader_key], selected_client_name)
                            data_to_save_batch.append([timestamp, selected_client_name, "Compra", row_data["pesos_pagar"], row_data["usdt_recibir"], precio_compra_casa, link_compra])
                        
                        if row_data["pesos_cobrar"] > 0 or row_data["usdt_entregar"] > 0:
                            link_venta = ""
                            uploader_key = f"uploader_compra_{i}"
                            if uploader_key in st.session_state and st.session_state[uploader_key] is not None:
                                link_venta = upload_to_dropbox(dbx_client, st.session_state[uploader_key], selected_client_name)
                            data_to_save_batch.append([timestamp, selected_client_name, "Venta", row_data["pesos_cobrar"], row_data["usdt_entregar"], precio_venta_casa, link_venta])

                    # Procesar filas de ajustes
                    for i, ajuste in enumerate(all_ajustes_data):
                        if ajuste['pago_monto'] > 0:
                            link_pago = ""
                            uploader_key = f"uploader_pago_{i}"
                            if uploader_key in st.session_state and st.session_state[uploader_key] is not None:
                               link_pago = upload_to_dropbox(dbx_client, st.session_state[uploader_key], selected_client_name)
                            pesos = ajuste['pago_monto'] if ajuste['pago_moneda'] == 'MXN' else ""
                            usdt = ajuste['pago_monto'] if ajuste['pago_moneda'] == 'USDT' else ""
                            data_to_save_batch.append([timestamp, selected_client_name, "Pago", pesos, usdt, "N/A", link_pago])

                        if ajuste['recibo_monto'] > 0:
                            link_recibo = ""
                            uploader_key = f"uploader_recibo_{i}"
                            if uploader_key in st.session_state and st.session_state[uploader_key] is not None:
                                link_recibo = upload_to_dropbox(dbx_client, st.session_state[uploader_key], selected_client_name)
                            pesos = ajuste['recibo_monto'] if ajuste['recibo_moneda'] == 'MXN' else ""
                            usdt = ajuste['recibo_monto'] if ajuste['recibo_moneda'] == 'USDT' else ""
                            data_to_save_batch.append([timestamp, selected_client_name, "Recibo", pesos, usdt, "N/A", link_recibo])
                    
                    if not data_to_save_batch:
                        st.warning("No hay operaciones con montos mayores a cero para guardar.")
                    else:
                        try:
                            spreadsheet = gsheet_client.open_by_key(SPREADSHEET_ID)
                            sheet = spreadsheet.worksheet(SHEET_TAB_NAME)
                            sheet.append_rows(data_to_save_batch, value_input_option='USER_ENTERED')
                            
                            update_success = update_client_balance(gsheet_client, SPREADSHEET_ID, selected_client_name, balance_final_usdt, balance_final_pesos)
                            
                            if update_success:
                                st.success(f"✅ ¡Éxito! Se guardaron {len(data_to_save_batch)} operaciones y se actualizó el saldo.")
                            else:
                                st.success(f"✅ ¡Éxito! Se guardaron {len(data_to_save_batch)} operaciones.")
                            st.balloons()
                        except Exception as e:
                            st.error(f"❌ Error al guardar: {e}")
                            
    with col_clear_all:
        st.button("🔄 Limpiar Todo", use_container_width=True, on_click=limpiar_todo_callback)

if __name__ == "__main__":
    main()