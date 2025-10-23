import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import dropbox
import os
import pytz

# --- Importar credenciales (solo para entorno local) ---
try:
    from config import GOOGLE_CREDS, SPREADSHEET_ID, SHEET_TAB_NAME
except ImportError:
    pass

# --- FUNCIONES DE CONEXIÓN Y DATOS ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]

@st.cache_resource
def connect_to_google_sheets():
    try:
        creds_dict = st.secrets["google_creds"]
        spreadsheet_id = st.secrets["SPREADSHEET_ID"]
        sheet_tab_name = st.secrets["SHEET_TAB_NAME"]
    except (FileNotFoundError, KeyError):
        creds_dict = GOOGLE_CREDS
        spreadsheet_id = SPREADSHEET_ID
        sheet_tab_name = SHEET_TAB_NAME
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client, spreadsheet_id, sheet_tab_name

@st.cache_resource
def connect_to_dropbox():
    try:
        token = st.secrets["DROPBOX_ACCESS_TOKEN"]
    except (FileNotFoundError, KeyError):
        token = "sl.u.AGDSm9m01Pu9PerzbXzxu_f7oOHGMPFhZ4GbxXMIbloaWgYbM380tFReJk78H86bo-IDzC5tzYVQxe4SFUPTmjJbf1tMA1Hu1vQUHG8SKjTewqwUSlehHjdYw-y-r2fsNcYwg9OlZ9NIxKg7_M5UHnG2B_mqrvkA1bdQ45hF_BeGJzcRMXHdMpfa6nhvm6AXWDJPUrLIP8ohg-R-oYuC4Ghs_4iefKiMGel3nLyY29_BCOqqJPtZ_u4eRaR_r6IZcIIaSrFbzpNrJsrxCgHk0W4HdFmYGdL8UyL1zr8fBt7ZcUTl1AHtPN7XgLohnoCjfW876gOv-pBZ9MATHUNTkbg4PHuQYJIpuaNbuCkT4LG-PZW1S3-LEoy2qZWJfCHtbrJGPayvLIJ2VTM1xRU05RkC3zUVN06fcfWyzzM5i04ymslSrtZChb4JgV3hYVKGOBJ30f9TCkfm68dLL9s-Y_xQj5Kis3cFc-RxgF711tSXjTzCflLBHSD4QhhJ7dbtorSooDKgaG27GTDUH4H82IKsdGUTnWJK2VLLHv3aAN-gHQ_D4oW-2JCx7odr0G_-LxndNtOAAOA_E_xEsXRjXHnKllugDGVnUTHhDLZOok3f5JP25g1v8U0PczGXPaxtv1_j31WJWp1d4clx70zkTu_UMB3Vd4B7hkjR6sx45IsclrWcy54_bMYwHb3kcZrtYwB8LyT11Ur_O4klzxsCOPy_e6PIoFNI9-ULSEVcKz1PwT87Y2o12bEzsc65PzgRdV-2dpLDZzXyfHY_e0ZqCsVMt4JMbG-RmqJ_LmnXLoNEvvC3rvv1rhBPAetLOCckHvhvsq1q-TCuzJx7P-in1rgJW3tVYncxmtnpBSGJFsbHLDWw2K7rSOFLuyCwRBMfsVArYGz8Omu70dY6tn8rbxb2ClpjpL4jlMZ6M-M8tL2ex9ImqlCZflkfkWSdbtcgXqBu9eaLnVMF9qPtxi8UUAAEw3OcFewTuj273LMiJqXlq4Ofpt_qjCpkWFVnw35dqwMUH7uNlsFxj-CJU2GAcuaRwuU0S77jbR8Aownx7guOvXPCLm9v3_irRFq9OfDEotYQFPlBSjIiRTk9ZhgjCRshwKDQpET7dk-XoNmerPa6H-g74u9YVFAYkeYS2EV7CiguK8u9yt3Bsgu8yhF7DE_cwOYr8yG7dpG8nDCfXcD8jPvL9iQM1BIYpDPxTbE4ViE1W9qmPRZZ3aDBazJck7Vn6He4Eul9UIY-CJRBfuGJo1boK_CMAPj4MrJNscgypr0UpOm4Si9Dci3WFtbPcsF9Ihaw2aXB0TrEm3PnwxbR_xPDKAnU8KHL8OFPYPbPJB0_3IwZ0syfe_KKNQVk-I5_-xHlGKuwkj4O_bHsnhF-6NroNdVz_CIA-Qy_mkB4rPyIAtHJOmalwXoWgGKn4aSKMvzGYfmqSQv8YbUN_UZzyqrYx8glk0c7gpWse97rfJrxZpEvaCOVbYgtpUrLwueLRt9uMgJkPPavprDDDNZrOQ"
        return dropbox.Dropbox(token)

@st.cache_data(ttl=60)
def get_client_data(_gsheet_client, spreadsheet_id):
    try:
        spreadsheet = _gsheet_client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet("Clientes")
        data = worksheet.get_all_records()
        if not data: return pd.DataFrame(columns=['Alias Cliente', 'Saldo USDT'])
        df = pd.DataFrame(data)
        df['Saldo USDT'] = df['Saldo USDT'].astype(str).str.replace(r'[$,]', '', regex=True)
        df['Saldo USDT'] = pd.to_numeric(df['Saldo USDT'], errors='coerce').fillna(0)
        return df
    except gspread.exceptions.WorksheetNotFound:
        st.error("Error: No se encontró la hoja 'Clientes' en tu Google Sheet.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"No se pudo cargar la lista de clientes: {e}")
        return pd.DataFrame()

def upload_to_dropbox(dbx_client, file_object, client_name):
    try:
        mexico_tz = pytz.timezone("America/Mexico_City")
        timestamp = datetime.now(mexico_tz).strftime("%Y%m%d_%H%M%S")
        dropbox_path = f"/{client_name.replace(' ', '_')}/{timestamp}_{file_object.name}"
        dbx_client.files_upload(file_object.getvalue(), dropbox_path, mode=dropbox.files.WriteMode('overwrite'))
        link_metadata = dbx_client.sharing_create_shared_link_with_settings(dropbox_path)
        link = link_metadata.url
        return link.replace("?dl=0", "?raw=1")
    except Exception as e:
        st.warning(f"No se pudo subir el archivo a Dropbox: {e}")
        return ""

def update_client_balance(_gsheet_client, spreadsheet_id, client_alias, new_usdt):
    try:
        spreadsheet = _gsheet_client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet("Clientes")
        cell = worksheet.find(client_alias, in_column=2)
        if cell is None:
            st.warning(f"No se pudo encontrar al cliente '{client_alias}' para actualizar su saldo.")
            return False
        headers = worksheet.row_values(1)
        usdt_col = headers.index("Saldo USDT") + 1
        worksheet.update_cell(cell.row, usdt_col, new_usdt)
        return True
    except Exception as e:
        st.warning(f"Hubo un error al actualizar el saldo del cliente: {e}")
        return False

def get_next_folio_number(_gsheet_client, spreadsheet_id, sheet_tab_name):
    try:
        spreadsheet = _gsheet_client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_tab_name)
        all_values = worksheet.get_all_values()
        if len(all_values) < 2: return 1
        last_row = all_values[-1]
        last_folio = last_row[0]
        parts = last_folio.split('-')
        last_folio_date_str = f"{parts[0]}-{parts[1]}-{parts[2]}"
        last_folio_num = int(parts[3])
        today_date_str = datetime.now(pytz.timezone("America/Mexico_City")).strftime("%y-%m-%d")
        if last_folio_date_str == today_date_str:
            return last_folio_num + 1
        else:
            return 1
    except (ValueError, IndexError, gspread.exceptions.WorksheetNotFound):
        return 1
    except Exception:
        return 1

# --- FUNCIONES DE LA INTERFAZ ---

# Reemplaza tu función create_calculation_row existente con esta:
def create_calculation_row(row_index, comision_compra, comision_venta, mode_compra, mode_venta):
    col_compra, _, col_venta = st.columns([1, 0.2, 1])
    
    key_iter = st.session_state.get('upload_key_iter', 0)

    usd_compra_final, usdt_compra_final, input_compra = 0.0, 0.0, 0.0
    usd_venta_final, usdt_venta_final, input_venta = 0.0, 0.0, 0.0

    with col_compra:
        if row_index == 0: st.subheader("Compra (Tú das USD)")
        
        input_col, result_col, upload_col = st.columns([0.45, 0.3, 0.25])

        with input_col:
            label_visibility = "visible" if row_index == 0 else "collapsed"
            if mode_compra == "USD ➔ USDT":
                input_label = "Monto en USD que das"
                input_compra = st.number_input(input_label, min_value=0.0, format="%.2f", step=100.0, key=f"input_compra_{row_index}", label_visibility=label_visibility)
            else:
                input_label = "Monto en USDT a recibir"
                input_compra = st.number_input(input_label, min_value=0.0, format="%.2f", step=100.0, key=f"input_compra_{row_index}", label_visibility=label_visibility)
        
        if mode_compra == "USD ➔ USDT":
            usd_compra_final, usdt_compra_final = input_compra, input_compra * (1 - comision_compra / 100)
            # --- CAMBIO AQUÍ: Se usa padding-top para forzar la alineación ---
            resultado_texto = f"<p style='font-size: 28px; font-weight: bold; color: #228B22; margin: 0; padding-top: 15px;'>{usdt_compra_final:,.2f} USDT</p>"
        else:
            usdt_compra_final = input_compra
            usd_compra_final = usdt_compra_final / (1 - comision_compra / 100) if comision_compra < 100 else 0
            # --- CAMBIO AQUÍ: Se usa padding-top para forzar la alineación ---
            resultado_texto = f"<p style='font-size: 28px; font-weight: bold; color: #DC143C; margin: 0; padding-top: 15px;'>{usd_compra_final:,.2f} USD</p>"
        
        with result_col:
            st.markdown(resultado_texto, unsafe_allow_html=True)

        with upload_col:
            st.file_uploader("Comp.", type=["png", "jpg", "jpeg", "pdf"], key=f"uploader_compra_{row_index}_{key_iter}", label_visibility="collapsed")

    with col_venta:
        if row_index == 0: st.subheader("Venta (Tú recibes USD)")
        
        input_col, result_col, upload_col = st.columns([0.45, 0.3, 0.25])
        
        with input_col:
            label_visibility = "visible" if row_index == 0 else "collapsed"
            if mode_venta == "USD ➔ USDT":
                input_label = "Monto en USD que recibes"
                input_venta = st.number_input(input_label, min_value=0.0, format="%.2f", step=100.0, key=f"input_venta_{row_index}", label_visibility=label_visibility)
            else:
                input_label = "Monto en USDT a dar"
                input_venta = st.number_input(input_label, min_value=0.0, format="%.2f", step=100.0, key=f"input_venta_{row_index}", label_visibility=label_visibility)

        if mode_venta == "USD ➔ USDT":
            usd_venta_final, usdt_venta_final = input_venta, input_venta * (1 - comision_venta / 100)
            # --- CAMBIO AQUÍ: Se usa padding-top para forzar la alineación ---
            resultado_texto = f"<p style='font-size: 28px; font-weight: bold; color: #DC143C; margin: 0; padding-top: 27px;'>{usdt_venta_final:,.2f} USDT</p>"
        else:
            usdt_venta_final = input_venta
            usd_venta_final = usdt_venta_final / (1 - comision_venta / 100) if comision_venta < 100 else 0
            # --- CAMBIO AQUÍ: Se usa padding-top para forzar la alineación ---
            resultado_texto = f"<p style='font-size: 28px; font-weight: bold; color: #228B22; margin: 0; padding-top: 27px;'>{usd_venta_final:,.2f} USD</p>"

        with result_col:
            st.markdown(resultado_texto, unsafe_allow_html=True)
            
        with upload_col:
            st.file_uploader("Comp.", type=["png", "jpg", "jpeg", "pdf"], key=f"uploader_venta_{row_index}_{key_iter}", label_visibility="collapsed")
        
    return {
        "usd_dados_compra": usd_compra_final, "usdt_recibidos_compra": usdt_compra_final,
        "usd_recibidos_venta": usd_venta_final, "usdt_dados_venta": usdt_venta_final,
    }

# <-- FUNCIÓN REESCRITA para layout compacto y reseteo de archivos
def create_ajuste_row(row_index):
    col_pago, _, col_recibo = st.columns([1, 0.2, 1])
    key_iter = st.session_state.get('upload_key_iter', 0)
    
    with col_pago:
        if row_index == 0: st.subheader("Pagos (Salidas)")
        input_col, upload_col = st.columns([0.7, 0.3])
        with input_col:
            pago_monto = st.number_input("Monto del Pago", min_value=0.0, format="%.2f", key=f"pago_monto_{row_index}", label_visibility="visible" if row_index == 0 else "collapsed")
        with upload_col:
            st.file_uploader("Comp. Pago", type=["png", "jpg", "jpeg", "pdf"], key=f"uploader_pago_{row_index}_{key_iter}", label_visibility="collapsed")

    with col_recibo:
        if row_index == 0: st.subheader("Recibos (Entradas)")
        input_col, upload_col = st.columns([0.7, 0.3])
        with input_col:
            recibo_monto = st.number_input("Monto del Recibo", min_value=0.0, format="%.2f", key=f"recibo_monto_{row_index}", label_visibility="visible" if row_index == 0 else "collapsed")
        with upload_col:
            st.file_uploader("Comp. Recibo", type=["png", "jpg", "jpeg", "pdf"], key=f"uploader_recibo_{row_index}_{key_iter}", label_visibility="collapsed")
            
    return {"pago_usdt": pago_monto, "recibo_usdt": recibo_monto}

def main():
    st.set_page_config(page_title="Calculadora USD/USDT", page_icon="🏦", layout="wide")
    st.markdown("""
    <style>
        [data-testid="stFileUploader"] section [data-testid="stFileUploaderDropzone"] {display: none;}
        [data-testid="stFileUploader"] section {padding: 0;border: none;}
        [data-testid="stFileUploader"] {padding-top: 28px;}
        h6 { margin-bottom: 0px; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Calculadora USD-USDT 🏦</h1>", unsafe_allow_html=True)
    st.markdown("---")
    gsheet_client, SPREADSHEET_ID, SHEET_TAB_NAME = connect_to_google_sheets()
    dbx_client = connect_to_dropbox()

    # Se inicializa un iterador de clave para el reseteo de los uploaders
    if 'upload_key_iter' not in st.session_state:
        st.session_state.upload_key_iter = 0

    def add_calculo_row(): st.session_state.num_rows = st.session_state.get('num_rows', 1) + 1
    def add_ajuste_row(): st.session_state.num_ajustes = st.session_state.get('num_ajustes', 1) + 1
    
    # <-- CALLBACKS DE LIMPIEZA SIMPLIFICADOS ---
    def limpiar_calculos_callback():
        for i in range(st.session_state.get('num_rows', 1)):
            if f"input_compra_{i}" in st.session_state:
                st.session_state[f"input_compra_{i}"] = 0.0
            if f"input_venta_{i}" in st.session_state:
                st.session_state[f"input_venta_{i}"] = 0.0
        st.session_state.num_rows = 1
        st.session_state.upload_key_iter += 1 # Incrementar el iterador fuerza el reseteo de los uploaders
    
    def limpiar_ajustes_callback():
            # Se reintroduce el código para limpiar los campos de texto
        for i in range(st.session_state.get('num_ajustes', 1)):
            if f"pago_monto_{i}" in st.session_state:
                st.session_state[f"pago_monto_{i}"] = 0.0
            if f"recibo_monto_{i}" in st.session_state:
                st.session_state[f"recibo_monto_{i}"] = 0.0
        st.session_state.num_ajustes = 1
        st.session_state.upload_key_iter += 1 # Incrementar el iterador fuerza el reseteo de los uploaders

    def limpiar_todo_callback():
        limpiar_calculos_callback()
        limpiar_ajustes_callback()
        st.session_state.num_rows = 1
        st.session_state.num_ajustes = 1
        if "cliente_selector" in st.session_state: st.session_state.cliente_selector = "-- Seleccione un Cliente --"
        st.session_state.upload_key_iter += 1 # Reseteo global de todos los uploaders

    # El resto del código `main` sigue aquí...
    # --- SECCIÓN 1: CONFIGURACIÓN ---
    st.header("1. Configuración de Operación")
    col_cliente, col_compra, col_venta = st.columns(3)
    with col_cliente:
        st.subheader("Cliente")
        client_df = get_client_data(gsheet_client, SPREADSHEET_ID)
        balance_inicial_usdt, selected_client_name = 0.0, ""
        if not client_df.empty:
            client_list = ["-- Seleccione un Cliente --"] + client_df['Alias Cliente'].tolist()
            selected_client_name = st.selectbox("Cliente", client_list, key="cliente_selector")
            if selected_client_name != "-- Seleccione un Cliente --":
                client_data = client_df[client_df['Alias Cliente'] == selected_client_name].iloc[0]
                balance_inicial_usdt = float(client_data['Saldo USDT'])
                st.metric("Saldo Actual USDT", f"{balance_inicial_usdt:,.2f}")
                st.caption("Positivo = cliente te debe. Negativo = tú le debes.")
    with col_compra:
        st.subheader("Config. Compra (Tú das USD)")
        comision_compra = st.number_input("Comisión de Compra (%)", value=3.50, min_value=0.0, format="%.2f", step=0.5, key="comision_compra_input")
        mode_compra = st.radio("Modo de Cálculo", ("USD ➔ USDT", "USDT ➔ USD"), horizontal=True, key="mode_compra")
    with col_venta:
        st.subheader("Config. Venta (Tú recibes USD)")
        comision_venta = st.number_input("Comisión de Venta (%)", value=4.50, min_value=0.0, format="%.2f", step=0.5, key="comision_venta_input")
        mode_venta = st.radio("Modo de Cálculo", ("USD ➔ USDT", "USDT ➔ USD"), horizontal=True, key="mode_venta")
    st.markdown("---")

    # --- SECCIÓN 2: OPERACIONES ---
    st.header("2. Operaciones de Compra/Venta")
    if 'num_rows' not in st.session_state: st.session_state.num_rows = 1
    bcol1, bcol2, _ = st.columns([0.2, 0.2, 1.6], gap="small")
    with bcol1: st.button("➕ Añadir Fila", on_click=add_calculo_row)
    with bcol2: st.button("🔄 Limpiar Filas", on_click=limpiar_calculos_callback)
    all_rows_data = [create_calculation_row(i, comision_compra, comision_venta, mode_compra, mode_venta) for i in range(st.session_state.num_rows)]
    st.markdown("---")
    
    # --- SECCIÓN 3: AJUSTES DE CAJA ---
    st.header("3. Ajustes de Caja")
    if 'num_ajustes' not in st.session_state: st.session_state.num_ajustes = 1
    acol1, acol2, _ = st.columns([0.2, 0.2, 1.6], gap="small")
    with acol1: st.button("➕ Añadir Ajuste", on_click=add_ajuste_row)
    with acol2: st.button("🔄 Limpiar Ajustes", on_click=limpiar_ajustes_callback)
    all_ajustes_data = [create_ajuste_row(i) for i in range(st.session_state.num_ajustes)]
    st.markdown("---")

    # --- SECCIÓN 4: TOTALES Y BALANCE ---
    st.header("4. Totales y Balance Final")
    total_usdt_recibidos_op = sum(d['usdt_recibidos_compra'] for d in all_rows_data)
    total_usdt_entregados_op = sum(d['usdt_dados_venta'] for d in all_rows_data)
    total_usdt_pagos_ajuste = sum(d['pago_usdt'] for d in all_ajustes_data)
    total_usdt_recibos_ajuste = sum(d['recibo_usdt'] for d in all_ajustes_data)
    st.subheader("Totales Consolidados 🧮")
    col_t1, col_t2 = st.columns(2)
    with col_t1: st.metric("TOTAL USDT RECIBIDOS (Op. + Ajustes)", f"{total_usdt_recibidos_op + total_usdt_pagos_ajuste:,.2f} USDT")
    with col_t2: st.metric("TOTAL USDT ENTREGADOS (Op. + Ajustes)", f"{total_usdt_entregados_op + total_usdt_recibos_ajuste:,.2f} USDT")
    st.subheader("Balance Final de Cierre del Cliente ⚖️")
    cambio_neto_usdt = (total_usdt_recibidos_op + total_usdt_pagos_ajuste) - (total_usdt_entregados_op + total_usdt_recibos_ajuste)
    balance_final_usdt = balance_inicial_usdt + cambio_neto_usdt
    st.metric("Nuevo Saldo USDT del Cliente", f"{balance_final_usdt:,.2f}", delta=f"{cambio_neto_usdt:,.2f} USDT")
    if balance_final_usdt > 0.01: status_texto, status_color = "EL CLIENTE TE DEBE", "#228B22"
    elif balance_final_usdt < -0.01: status_texto, status_color = "TÚ LE DEBES AL CLIENTE", "#DC143C"
    else: status_texto, status_color = "SALDO CERO", "gray"
    st.markdown(f"<h3 style='text-align: center; color: {status_color};'>{status_texto}</h3>", unsafe_allow_html=True)
    st.markdown("---")

    # --- SECCIÓN 5: REGISTRO ---
    st.header("5. Registrar Operaciones")
    col_save, col_clear_all = st.columns([3,1])
    with col_save:
        if st.button("💾 Guardar y Actualizar Saldo", use_container_width=True, type="primary"):
            if not selected_client_name or selected_client_name == "-- Seleccione un Cliente --":
                st.error("Por favor, seleccione un cliente antes de guardar.")
            else:
                operations_to_process = []
                # Re-evaluar los montos en el momento del click para asegurar datos frescos
                current_key_iter = st.session_state.get('upload_key_iter', 0)
                for i in range(st.session_state.get('num_rows', 1)):
                    if st.session_state.get(f"input_compra_{i}", 0) > 0:
                        operations_to_process.append({'type': 'Compra', 'index': i})
                    if st.session_state.get(f"input_venta_{i}", 0) > 0:
                        operations_to_process.append({'type': 'Venta', 'index': i})
                for i in range(st.session_state.get('num_ajustes', 1)):
                    if st.session_state.get(f"pago_monto_{i}", 0) > 0:
                        operations_to_process.append({'type': 'Ajuste-Pago', 'index': i})
                    if st.session_state.get(f"recibo_monto_{i}", 0) > 0:
                        operations_to_process.append({'type': 'Ajuste-Recibo', 'index': i})

                if not operations_to_process:
                    st.warning("No hay operaciones o ajustes con montos mayores a cero para guardar.")
                else:
                    progress_bar = st.progress(0, text="Iniciando guardado...")
                    mexico_tz = pytz.timezone("America/Mexico_City")
                    now_mexico = datetime.now(mexico_tz)
                    timestamp = now_mexico.strftime("%Y-%m-%d %H:%M:%S")
                    today_prefix = now_mexico.strftime("%y-%m-%d")
                    next_folio_num = get_next_folio_number(gsheet_client, SPREADSHEET_ID, SHEET_TAB_NAME)
                    data_to_save_batch = []
                    total_ops = len(operations_to_process)
                    
                    for i, op in enumerate(operations_to_process):
                        current_folio = f"{today_prefix}-{next_folio_num + i:04d}"
                        progress_text = f"Procesando operación {current_folio}..."
                        progress_bar.progress((i + 1) / (total_ops + 2), text=progress_text)
                        link, file_to_upload = "", None

                        # --- CAMBIO IMPORTANTE: Se obtiene el archivo usando la key dinámica ---
                        if op['type'] == 'Compra':
                            file_to_upload = st.session_state.get(f"uploader_compra_{op['index']}_{current_key_iter}")
                            row_data = all_rows_data[op['index']]
                            if file_to_upload: link = upload_to_dropbox(dbx_client, file_to_upload, selected_client_name)
                            data_to_save_batch.append([current_folio, timestamp, selected_client_name, "Compra (Das USD)", row_data['usd_dados_compra'], row_data['usdt_recibidos_compra'], comision_compra, link])
                        elif op['type'] == 'Venta':
                            file_to_upload = st.session_state.get(f"uploader_venta_{op['index']}_{current_key_iter}")
                            row_data = all_rows_data[op['index']]
                            if file_to_upload: link = upload_to_dropbox(dbx_client, file_to_upload, selected_client_name)
                            data_to_save_batch.append([current_folio, timestamp, selected_client_name, "Venta (Recibes USD)", row_data['usd_recibidos_venta'], row_data['usdt_dados_venta'], comision_venta, link])
                        elif op['type'] == 'Ajuste-Pago':
                            file_to_upload = st.session_state.get(f"uploader_pago_{op['index']}_{current_key_iter}")
                            row_data = all_ajustes_data[op['index']]
                            if file_to_upload: link = upload_to_dropbox(dbx_client, file_to_upload, selected_client_name)
                            data_to_save_batch.append([current_folio, timestamp, selected_client_name, "Ajuste: Pago Cliente", "", row_data['pago_usdt'], "N/A", link])
                        elif op['type'] == 'Ajuste-Recibo':
                            file_to_upload = st.session_state.get(f"uploader_recibo_{op['index']}_{current_key_iter}")
                            row_data = all_ajustes_data[op['index']]
                            if file_to_upload: link = upload_to_dropbox(dbx_client, file_to_upload, selected_client_name)
                            data_to_save_batch.append([current_folio, timestamp, selected_client_name, "Ajuste: Recibo Tuyo", "", row_data['recibo_usdt'], "N/A", link])
                    try:
                        progress_bar.progress((total_ops + 1) / (total_ops + 2), text="Guardando en Google Sheets...")
                        sheet = gsheet_client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_TAB_NAME)
                        sheet.append_rows(data_to_save_batch, value_input_option='USER_ENTERED')
                        progress_bar.progress(1.0, text="Actualizando saldo del cliente...")
                        update_success = update_client_balance(gsheet_client, SPREADSHEET_ID, selected_client_name, balance_final_usdt)
                        progress_bar.empty()
                        if update_success:
                            st.success(f"✅ ¡Éxito! Se guardaron las operaciones y se actualizó el saldo.")
                        else:
                            st.error(f"Se guardaron las operaciones, pero hubo un error al actualizar el saldo del cliente.")
                        st.balloons()
                    except Exception as e:
                        progress_bar.empty()
                        st.error(f"❌ Error al guardar: {e}")
    with col_clear_all:
        st.button("🔄 Limpiar Todo", on_click=limpiar_todo_callback, use_container_width=True)

if __name__ == "__main__":
    main()