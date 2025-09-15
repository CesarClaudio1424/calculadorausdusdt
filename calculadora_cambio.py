import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- Importar credenciales y ID desde el archivo de configuración ---
from config import GOOGLE_CREDS, SPREADSHEET_ID, SHEET_TAB_NAME

# --- FUNCIONES DE CONEXIÓN ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]

@st.cache_resource
def connect_to_google_sheets():
    """Conecta a Google Sheets usando las credenciales del archivo config.py."""
    creds = Credentials.from_service_account_info(GOOGLE_CREDS, scopes=SCOPES)
    return gspread.authorize(creds)

# --- FIN DE FUNCIONES DE CONEXIÓN ---


def create_calculation_row(row_index, precio_compra, precio_venta, mode_vende, mode_compra):
    """
    Crea una fila de cálculo y devuelve un diccionario con sus datos.
    """
    div_height = 78 if row_index == 0 else 38
    
    col_vende, _, col_compra = st.columns([1, 0.2, 1])

    if row_index == 0:
        with col_vende:
            st.subheader("Cliente Vende / Yo Compro") # Título restaurado en la interfaz
        with col_compra:
            st.subheader("Cliente Compra / Yo Vendo") # Título restaurado en la interfaz

    # --- SECCIÓN IZQUIERDA (Yo Compro) ---
    with col_vende:
        label_vende = "Monto en USDT a Recibir" if mode_vende == "USDT -> Pesos" else "Monto en Pesos a Pagar"
        resultado_suffix_vende = "MXN" if mode_vende == "USDT -> Pesos" else "USDT"

        col_monto_input, col_resultado_output = st.columns([1, 1])
        with col_monto_input:
            label_visibility = "visible" if row_index == 0 else "collapsed"
            input_vende = st.number_input(label_vende, min_value=0.0, format="%.2f", step=100.0,
                                          key=f"input_vende_{row_index}", label_visibility=label_visibility)
        with col_resultado_output:
            if mode_vende == "Pesos -> USDT":
                pesos_a_pagar = input_vende
                usdt_a_recibir = (pesos_a_pagar / precio_compra) if precio_compra > 0 else 0.0
                resultado_vende = usdt_a_recibir
            else: 
                usdt_a_recibir = input_vende
                pesos_a_pagar = usdt_a_recibir * precio_compra
                resultado_vende = pesos_a_pagar
            
            st.markdown(f"""<div style="display: flex; align-items: center; justify-content: start; height: {div_height}px;"><p style='font-size: 28px; font-weight: bold; color: #228B22; margin: 0;'>{resultado_vende:,.2f} {resultado_suffix_vende}</p></div>""", unsafe_allow_html=True)

    # --- SECCIÓN DERECHA (Yo Vendo) ---
    with col_compra:
        label_compra = "Monto en USDT a Entregar" if mode_compra == "USDT -> Pesos" else "Monto en Pesos a Cobrar"
        resultado_suffix_compra = "MXN" if mode_compra == "USDT -> Pesos" else "USDT"

        col_monto_input, col_resultado_output = st.columns([1, 1])
        with col_monto_input:
            label_visibility = "visible" if row_index == 0 else "collapsed"
            input_compra = st.number_input(label_compra, min_value=0.0, format="%.2f", step=100.0,
                                           key=f"input_compra_{row_index}", label_visibility=label_visibility)
        with col_resultado_output:
            if mode_compra == "Pesos -> USDT":
                pesos_a_cobrar = input_compra
                usdt_a_entregar = (pesos_a_cobrar / precio_venta) if precio_venta > 0 else 0.0
                resultado_compra = usdt_a_entregar
            else:
                usdt_a_entregar = input_compra
                pesos_a_cobrar = usdt_a_entregar * precio_venta
                resultado_compra = pesos_a_cobrar
            
            st.markdown(f"""<div style="display: flex; align-items: center; justify-content: start; height: {div_height}px;"><p style='font-size: 28px; font-weight: bold; color: #DC143C; margin: 0;'>{resultado_compra:,.2f} {resultado_suffix_compra}</p></div>""", unsafe_allow_html=True)
    
    return {
        "pesos_pagar": pesos_a_pagar, "usdt_recibir": usdt_a_recibir,
        "pesos_cobrar": pesos_a_cobrar, "usdt_entregar": usdt_a_entregar
    }

def main():
    st.set_page_config(page_title="Calculadora y Registro", page_icon="🏦", layout="wide")
    st.markdown("<h1 style='text-align: center;'>Calculadora y Registro de Operaciones 🏦</h1>", unsafe_allow_html=True)
    st.markdown("---")

    gsheet_client = connect_to_google_sheets()

    st.write("### Mis Tasas del Día")
    col_yo_compro, _, col_yo_vendo = st.columns([1, 0.2, 1])
    with col_yo_compro:
        precio_compra_casa = st.number_input("Tasa de Compra (Yo Compro USDT)", value=18.5500, format="%.4f", key="precio_compra_input")
    with col_yo_vendo:
        precio_venta_casa = st.number_input("Tasa de Venta (Yo Vendo USDT)", value=19.4400, format="%.4f", key="precio_venta_input")
    st.markdown("---")

    st.write("#### Selecciona el Modo de Cálculo para cada Columna")
    col_modo_vende, _, col_modo_compra = st.columns([1, 0.2, 1])
    with col_modo_vende:
        mode_vende = st.radio("Modo para 'Cliente Vende / Yo Compro'", ("Pesos -> USDT", "USDT -> Pesos"), horizontal=True, key="mode_vende") # Título restaurado
    with col_modo_compra:
        mode_compra = st.radio("Modo para 'Cliente Compra / Yo Vendo'", ("Pesos -> USDT", "USDT -> Pesos"), horizontal=True, key="mode_compra") # Título restaurado
    st.markdown("---")

    if 'num_rows' not in st.session_state:
        st.session_state.num_rows = 1

    col1, col2, _ = st.columns([1.3, 1.3, 5])
    with col1:
        if st.button("➕ Añadir Fila", use_container_width=True):
            if st.session_state.num_rows < 15: st.session_state.num_rows += 1
            else: st.toast("Límite de 15 filas alcanzado.", icon="⚠️")
    with col2:
        if st.button("🔄 Limpiar", use_container_width=True):
            for i in range(st.session_state.num_rows):
                if f"input_vende_{i}" in st.session_state: st.session_state[f"input_vende_{i}"] = 0.0
                if f"input_compra_{i}" in st.session_state: st.session_state[f"input_compra_{i}"] = 0.0
            st.session_state.num_rows = 1

    st.markdown("<br>", unsafe_allow_html=True)
    
    all_rows_data = []
    for i in range(st.session_state.num_rows):
        row_data = create_calculation_row(i, precio_compra_casa, precio_venta_casa, mode_vende, mode_compra)
        all_rows_data.append(row_data)
        if i < st.session_state.num_rows - 1:
            st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    st.markdown("---")
    
    st.write("### Balance Inicial del Cliente (Opcional)")
    col_bal_pesos, col_bal_usdt = st.columns(2)
    with col_bal_pesos:
        tipo_balance_pesos = st.radio("Tipo de Balance (Pesos)", ("El cliente me debe", "Yo le debo al cliente"), horizontal=True, key="radio_pesos")
        monto_balance_pesos = st.number_input("Monto del Balance (Pesos)", min_value=0.0, format="%.2f", key="bal_pesos")
        balance_inicial_pesos = monto_balance_pesos if tipo_balance_pesos == "El cliente me debe" else -monto_balance_pesos
    with col_bal_usdt:
        tipo_balance_usdt = st.radio("Tipo de Balance (USDT)", ("El cliente me debe", "Yo le debo al cliente"), horizontal=True, key="radio_usdt")
        monto_balance_usdt = st.number_input("Monto del Balance (USDT)", min_value=0.0, format="%.2f", key="bal_usdt")
        balance_inicial_usdt = monto_balance_usdt if tipo_balance_usdt == "El cliente me debe" else -monto_balance_usdt

    st.markdown("---")
    
    pagar_pesos_sum = sum(d['pesos_pagar'] for d in all_rows_data)
    recibir_usdt_sum = sum(d['usdt_recibir'] for d in all_rows_data)
    cobrar_pesos_sum = sum(d['pesos_cobrar'] for d in all_rows_data)
    entregar_usdt_sum = sum(d['usdt_entregar'] for d in all_rows_data)

    st.header("Totales Consolidados 🧮")
    total_recibidos_usdt_final = recibir_usdt_sum + (balance_inicial_usdt if balance_inicial_usdt > 0 else 0)
    total_entregados_usdt_final = entregar_usdt_sum + (abs(balance_inicial_usdt) if balance_inicial_usdt < 0 else 0)
    col_total_pagar, _, col_total_cobrar = st.columns([1, 0.2, 1])
    with col_total_pagar:
        st.metric(label="TOTAL PESOS PAGADOS (Operaciones)", value=f"${pagar_pesos_sum:,.2f}")
        st.metric(label="TOTAL USDT RECIBIDOS (Op. + Saldo)", value=f"{total_recibidos_usdt_final:,.2f} USDT")
    with col_total_cobrar:
        st.metric(label="TOTAL PESOS COBRADOS (Operaciones)", value=f"${cobrar_pesos_sum:,.2f}")
        st.metric(label="TOTAL USDT ENTREGADOS (Op. + Saldo)", value=f"{total_entregados_usdt_final:,.2f} USDT")
        
    st.markdown("---")
    st.header("Balance Final de USDT ⚖️")
    balance_usdt = (recibir_usdt_sum + balance_inicial_usdt) - entregar_usdt_sum
    if balance_usdt > 0:
        status_texto = "TE DEBEN PAGAR (Utilidad en USDT)"
        status_color = "#228B22"
    elif balance_usdt < 0:
        status_texto = "DEBES PAGAR (Pérdida en USDT)"
        status_color = "#DC143C"
    else:
        status_texto = "BALANCE CERO"
        status_color = "gray"
    _, col_balance, _ = st.columns([1, 1.2, 1])
    with col_balance:
        st.metric(label="DIFERENCIA NETA DE USDT", value=f"{abs(balance_usdt):,.2f} USDT")
        st.markdown(f"<h3 style='text-align: center; color: {status_color};'>{status_texto}</h3>", unsafe_allow_html=True)
            
    st.markdown("---")
    st.header("Registrar Operaciones")
    if st.button("💾 Guardar Todas las Operaciones en Google Sheets", use_container_width=True, type="primary"):
        data_to_save_batch = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for row_data in all_rows_data:
            if row_data["pesos_pagar"] > 0 or row_data["usdt_recibir"] > 0:
                # El registro se mantiene simplificado
                data_to_save_batch.append([timestamp, "Compra", row_data["pesos_pagar"], row_data["usdt_recibir"], precio_compra_casa])
            if row_data["pesos_cobrar"] > 0 or row_data["usdt_entregar"] > 0:
                # El registro se mantiene simplificado
                data_to_save_batch.append([timestamp, "Venta", row_data["pesos_cobrar"], row_data["usdt_entregar"], precio_venta_casa])
        if not data_to_save_batch:
            st.warning("No hay operaciones con montos mayores a cero para guardar.")
        else:
            with st.spinner(f"Guardando {len(data_to_save_batch)} operaciones..."):
                try:
                    spreadsheet = gsheet_client.open_by_key(SPREADSHEET_ID)
                    sheet = spreadsheet.worksheet(SHEET_TAB_NAME)
                    sheet.append_rows(data_to_save_batch)
                    st.success(f"✅ ¡Éxito! Se guardaron {len(data_to_save_batch)} operaciones.")
                except Exception as e:
                    st.error(f"❌ Error al guardar: {e}")

if __name__ == "__main__":
    main()