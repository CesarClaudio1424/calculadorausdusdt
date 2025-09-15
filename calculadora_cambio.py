import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# --- FUNCIONES DE CONEXIÓN Y DATOS ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]

@st.cache_resource
def connect_to_google_sheets():
    """
    Conecta a Google Sheets. Usa los secretos de Streamlit si está desplegado,
    de lo contrario, usa el archivo config.py local.
    Devuelve el cliente de gspread, el ID de la hoja y el nombre de la pestaña.
    """
    try:
        creds_dict = st.secrets["google_creds"]
        spreadsheet_id = st.secrets["SPREADSHEET_ID"]
        sheet_tab_name = st.secrets["SHEET_TAB_NAME"]
    except FileNotFoundError:
        from config import GOOGLE_CREDS, SPREADSHEET_ID, SHEET_TAB_NAME
        creds_dict = GOOGLE_CREDS
        spreadsheet_id = SPREADSHEET_ID
        sheet_tab_name = SHEET_TAB_NAME
    except Exception as e:
        st.error(f"Error cargando la configuración. Asegúrate de que tus 'Secrets' en Streamlit Cloud o tu 'config.py' local estén correctos. Detalle: {e}")
        st.stop()
        
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    
    return client, spreadsheet_id, sheet_tab_name

@st.cache_data(ttl=60)
def get_client_data(_gsheet_client, spreadsheet_id):
    """Lee la hoja 'Clientes' y devuelve los datos como un DataFrame."""
    try:
        spreadsheet = _gsheet_client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet("Clientes")
        data = worksheet.get_all_records()
        if not data:
            return pd.DataFrame(columns=['Alias Cliente', 'Saldo USDT', 'Saldo MXN'])
            
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

# --- FUNCIONES DE LA INTERFAZ ---

def create_calculation_row(row_index, precio_compra, precio_venta, mode_vende, mode_compra):
    # (Esta función no cambia)
    pass

def create_ajuste_row(row_index):
    # (Esta función no cambia)
    pass

def main():
    st.set_page_config(page_title="Calculadora y Registro", page_icon="🏦", layout="wide")
    st.markdown("<h1 style='text-align: center;'>Calculadora y Registro de Operaciones 🏦</h1>", unsafe_allow_html=True)
    st.markdown("---")

    gsheet_client, SPREADSHEET_ID, SHEET_TAB_NAME = connect_to_google_sheets()

    # --- Callbacks (sin cambios) ---

    # --- 1. SECCIÓN DE CONFIGURACIÓN UNIFICADA ---
    st.header("1. Configuración de Operación")
    col_cliente, col_compra, col_venta = st.columns(3)

    with col_cliente:
        st.subheader("Cliente y Balance")
        client_df = get_client_data(gsheet_client, SPREADSHEET_ID)
        balance_inicial_usdt = 0.0
        balance_inicial_pesos = 0.0
        selected_client_name = ""

        if not client_df.empty:
            client_list = ["-- Seleccione un Cliente --"] + client_df['Alias Cliente'].tolist()
            selected_client_name = st.selectbox("Cliente", client_list, key="cliente_selector")
            
            if selected_client_name != "-- Seleccione un Cliente --":
                client_data = client_df[client_df['Alias Cliente'] == selected_client_name].iloc[0]
                balance_inicial_usdt = float(client_data['Saldo USDT'])
                balance_inicial_pesos = float(client_data['Saldo MXN'])
                
                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.metric("Saldo USDT", f"{balance_inicial_usdt:,.2f}")
                with metric_col2:
                    st.metric("Saldo Pesos", f"${balance_inicial_pesos:,.2f}")
                st.caption("Positivo = cliente te debe. Negativo = tú le debes.")
        else:
            st.warning("No se pudieron cargar los clientes.")
    
    with col_compra:
        st.subheader("Configuración de Compra")
        precio_compra_casa = st.number_input("Tasa de Compra (Yo Compro USDT)", value=18.5500, format="%.4f", key="precio_compra_input")
        mode_vende = st.radio("Modo para 'Cliente Vende / Yo Compro'", ("Pesos -> USDT", "USDT -> Pesos"), horizontal=True, key="mode_vende")

    with col_venta:
        st.subheader("Configuración de Venta")
        precio_venta_casa = st.number_input("Tasa de Venta (Yo Vendo USDT)", value=19.4400, format="%.4f", key="precio_venta_input")
        mode_compra = st.radio("Modo para 'Cliente Compra / Yo Vendo'", ("Pesos -> USDT", "USDT -> Pesos"), horizontal=True, key="mode_compra")
    
    st.markdown("---")

    # ... (El resto del código de la aplicación: secciones 2, 3, 4, 5 sin cambios, solo la sección 6 de guardado) ...
    
    # --- 6. REGISTRAR OPERACIONES ---
    st.header("6. Registrar Operaciones")
    col_save, col_clear_all = st.columns([3,1])
    with col_save:
        if st.button("💾 Guardar Todas las Operaciones en Google Sheets", use_container_width=True, type="primary"):
            if not selected_client_name or selected_client_name == "-- Seleccione un Cliente --":
                st.error("Por favor, seleccione un cliente antes de guardar.")
            else:
                # ... Lógica de preparación del batch para guardar ...
                with st.spinner(f"Guardando operaciones para {selected_client_name}..."):
                    try:
                        spreadsheet = gsheet_client.open_by_key(SPREADSHEET_ID)
                        sheet = spreadsheet.worksheet(SHEET_TAB_NAME)
                        sheet.append_rows(data_to_save_batch, value_input_option='USER_ENTERED')
                        st.success("✅ ¡Éxito! Operaciones guardadas.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Error al guardar: {e}")
    with col_clear_all:
        st.button("🔄 Limpiar Todo", use_container_width=True, on_click=limpiar_todo_callback)

if __name__ == "__main__":
    main()