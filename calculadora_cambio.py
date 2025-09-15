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
    """Crea una fila de la calculadora de cambio."""
    div_height = 78 if row_index == 0 else 38
    col_vende, _, col_compra = st.columns([1, 0.2, 1])

    if row_index == 0:
        with col_vende:
            st.subheader("Cliente Vende / Yo Compro")
        with col_compra:
            st.subheader("Cliente Compra / Yo Vendo")

    with col_vende:
        label_vende = "Monto en USDT a Recibir" if mode_vende == "USDT -> Pesos" else "Monto en Pesos a Pagar"
        resultado_suffix_vende = "MXN" if mode_vende == "USDT -> Pesos" else "USDT"
        col_monto_input, col_resultado_output = st.columns([1, 1])
        with col_monto_input:
            label_visibility = "visible" if row_index == 0 else "collapsed"
            input_vende = st.number_input(label_vende, min_value=0.0, format="%.2f", step=100.0, key=f"input_vende_{row_index}", label_visibility=label_visibility)
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

    with col_compra:
        label_compra = "Monto en USDT a Entregar" if mode_compra == "USDT -> Pesos" else "Monto en Pesos a Cobrar"
        resultado_suffix_compra = "MXN" if mode_compra == "USDT -> Pesos" else "USDT"
        col_monto_input, col_resultado_output = st.columns([1, 1])
        with col_monto_input:
            label_visibility = "visible" if row_index == 0 else "collapsed"
            input_compra = st.number_input(label_compra, min_value=0.0, format="%.2f", step=100.0, key=f"input_compra_{row_index}", label_visibility=label_visibility)
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
    
    return {"pesos_pagar": pesos_a_pagar, "usdt_recibir": usdt_a_recibir, "pesos_cobrar": pesos_a_cobrar, "usdt_entregar": usdt_a_entregar}

def create_ajuste_row(row_index):
    """Crea una fila para la sección de Pagos y Recibos."""
    col_pago, _, col_recibo = st.columns([1, 0.2, 1])
    
    if row_index == 0:
        with col_pago: st.subheader("Pagos (Salidas)")
        with col_recibo: st.subheader("Recibos (Entradas)")

    with col_pago:
        pago_monto = st.number_input("Monto del Pago", min_value=0.0, format="%.2f", key=f"pago_monto_{row_index}", label_visibility="collapsed")
        # CAMBIO: index=1 para que USDT sea el default
        pago_moneda = st.radio("Moneda del Pago", ["MXN", "USDT"], key=f"pago_moneda_{row_index}", horizontal=True, index=1)

    with col_recibo:
        recibo_monto = st.number_input("Monto del Recibo", min_value=0.0, format="%.2f", key=f"recibo_monto_{row_index}", label_visibility="collapsed")
        # CAMBIO: index=1 para que USDT sea el default
        recibo_moneda = st.radio("Moneda del Recibo", ["MXN", "USDT"], key=f"recibo_moneda_{row_index}", horizontal=True, index=1)
        
    return {"pago_monto": pago_monto, "pago_moneda": pago_moneda, "recibo_monto": recibo_monto, "recibo_moneda": recibo_moneda}

def main():
    st.set_page_config(page_title="Calculadora y Registro", page_icon="🏦", layout="wide")
    st.markdown("<h1 style='text-align: center;'>Calculadora y Registro de Operaciones 🏦</h1>", unsafe_allow_html=True)
    st.markdown("---")

    gsheet_client = connect_to_google_sheets()

    # --- FUNCIONES CALLBACK ---
    def add_calculo_row():
        if st.session_state.num_rows < 15: st.session_state.num_rows += 1
        else: st.toast("Límite de 15 filas alcanzado.", icon="⚠️")
            
    def add_ajuste_row():
        st.session_state.num_ajustes += 1

    def limpiar_calculos_callback():
        for i in range(st.session_state.num_rows):
            if f"input_vende_{i}" in st.session_state: st.session_state[f"input_vende_{i}"] = 0.0
            if f"input_compra_{i}" in st.session_state: st.session_state[f"input_compra_{i}"] = 0.0
        st.session_state.num_rows = 1

    def limpiar_ajustes_callback():
        for i in range(st.session_state.num_ajustes):
            if f"pago_monto_{i}" in st.session_state: st.session_state[f"pago_monto_{i}"] = 0.0
            # CAMBIO: Limpiar a USDT
            if f"pago_moneda_{i}" in st.session_state: st.session_state[f"pago_moneda_{i}"] = "USDT"
            if f"recibo_monto_{i}" in st.session_state: st.session_state[f"recibo_monto_{i}"] = 0.0
            # CAMBIO: Limpiar a USDT
            if f"recibo_moneda_{i}" in st.session_state: st.session_state[f"recibo_moneda_{i}"] = "USDT"
        st.session_state.num_ajustes = 1
    
    # --- INTERFAZ PRINCIPAL ---
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
        mode_vende = st.radio("Modo para 'Cliente Vende / Yo Compro'", ("Pesos -> USDT", "USDT -> Pesos"), horizontal=True, key="mode_vende")
    with col_modo_compra:
        mode_compra = st.radio("Modo para 'Cliente Compra / Yo Vendo'", ("Pesos -> USDT", "USDT -> Pesos"), horizontal=True, key="mode_compra")
    st.markdown("---")

    if 'num_rows' not in st.session_state: st.session_state.num_rows = 1
    col1, col2, _ = st.columns([1.3, 1.3, 5])
    with col1:
        # CAMBIO: Texto del botón reducido
        st.button("➕ Añadir Cálculo", on_click=add_calculo_row, use_container_width=True)
    with col2:
        # CAMBIO: Texto del botón reducido
        st.button("🔄 Limpiar Cálculos", use_container_width=True, on_click=limpiar_calculos_callback)
    st.markdown("<br>", unsafe_allow_html=True)
    all_rows_data = []
    for i in range(st.session_state.num_rows):
        row_data = create_calculation_row(i, precio_compra_casa, precio_venta_casa, mode_vende, mode_compra)
        all_rows_data.append(row_data)
        if i < st.session_state.num_rows - 1: st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("---")

    st.header("Pagos y Recibos (Ajustes de Caja)")
    if 'num_ajustes' not in st.session_state: st.session_state.num_ajustes = 1
    all_ajustes_data = []
    for i in range(st.session_state.num_ajustes):
        ajuste_data = create_ajuste_row(i)
        all_ajustes_data.append(ajuste_data)
    col_ajuste1, col_ajuste2, _ = st.columns([1.3, 1.3, 5])
    with col_ajuste1:
        # CAMBIO: Texto del botón reducido
        st.button("➕ Añadir Ajuste", on_click=add_ajuste_row, use_container_width=True)
    with col_ajuste2:
        # CAMBIO: Texto del botón reducido
        st.button("🔄 Limpiar Ajustes", use_container_width=True, on_click=limpiar_ajustes_callback)
    st.markdown("---")
    
    # ... El resto del código para calcular y mostrar totales, y para guardar, no necesita cambios ...
    
    pagar_pesos_sum = sum(d['pesos_pagar'] for d in all_rows_data)
    recibir_usdt_sum = sum(d['usdt_recibir'] for d in all_rows_data)
    cobrar_pesos_sum = sum(d['pesos_cobrar'] for d in all_rows_data)
    entregar_usdt_sum = sum(d['usdt_entregar'] for d in all_rows_data)
    ajuste_neto_pesos = sum(d['pago_monto'] for d in all_ajustes_data if d['pago_moneda'] == 'MXN') - sum(d['recibo_monto'] for d in all_ajustes_data if d['recibo_moneda'] == 'MXN')
    ajuste_neto_usdt = sum(d['pago_monto'] for d in all_ajustes_data if d['pago_moneda'] == 'USDT') - sum(d['recibo_monto'] for d in all_ajustes_data if d['recibo_moneda'] == 'USDT')
    
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
    st.header("Totales Consolidados 🧮")
    total_recibidos_usdt_final = recibir_usdt_sum + (balance_inicial_usdt if balance_inicial_usdt > 0 else 0) + (ajuste_neto_usdt if ajuste_neto_usdt > 0 else 0)
    total_entregados_usdt_final = entregar_usdt_sum + (abs(balance_inicial_usdt) if balance_inicial_usdt < 0 else 0) + (abs(ajuste_neto_usdt) if ajuste_neto_usdt < 0 else 0)
    col_total_pagar, _, col_total_cobrar = st.columns([1, 0.2, 1])
    with col_total_pagar:
        st.metric(label="TOTAL PESOS PAGADOS (Operaciones)", value=f"${pagar_pesos_sum:,.2f}")
        st.metric(label="TOTAL USDT RECIBIDOS (Op. + Saldos)", value=f"{total_recibidos_usdt_final:,.2f} USDT")
    with col_total_cobrar:
        st.metric(label="TOTAL PESOS COBRADOS (Operaciones)", value=f"${cobrar_pesos_sum:,.2f}")
        st.metric(label="TOTAL USDT ENTREGADOS (Op. + Saldos)", value=f"{total_entregados_usdt_final:,.2f} USDT")
        
    st.markdown("---")
    st.header("Balance Final de USDT ⚖️")
    balance_usdt = (recibir_usdt_sum + balance_inicial_usdt + ajuste_neto_usdt) - entregar_usdt_sum
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
                data_to_save_batch.append([timestamp, "Compra", row_data["pesos_pagar"], row_data["usdt_recibir"], precio_compra_casa])
            if row_data["pesos_cobrar"] > 0 or row_data["usdt_entregar"] > 0:
                data_to_save_batch.append([timestamp, "Venta", row_data["pesos_cobrar"], row_data["usdt_entregar"], precio_venta_casa])
        for ajuste in all_ajustes_data:
            if ajuste['pago_monto'] > 0:
                pesos = ajuste['pago_monto'] if ajuste['pago_moneda'] == 'MXN' else ""
                usdt = ajuste['pago_monto'] if ajuste['pago_moneda'] == 'USDT' else ""
                data_to_save_batch.append([timestamp, "Pago", pesos, usdt, "N/A"])
            if ajuste['recibo_monto'] > 0:
                pesos = ajuste['recibo_monto'] if ajuste['recibo_moneda'] == 'MXN' else ""
                usdt = ajuste['recibo_monto'] if ajuste['recibo_moneda'] == 'USDT' else ""
                data_to_save_batch.append([timestamp, "Recibo", pesos, usdt, "N/A"])
        if not data_to_save_batch:
            st.warning("No hay operaciones para guardar.")
        else:
            with st.spinner(f"Guardando {len(data_to_save_batch)} operaciones..."):
                try:
                    spreadsheet = gsheet_client.open_by_key(SPREADSHEET_ID)
                    sheet = spreadsheet.worksheet(SHEET_TAB_NAME)
                    sheet.append_rows(data_to_save_batch, value_input_option='USER_ENTERED')
                    st.success(f"✅ ¡Éxito! Se guardaron {len(data_to_save_batch)} operaciones.")
                except Exception as e:
                    st.error(f"❌ Error al guardar: {e}")

if __name__ == "__main__":
    main()