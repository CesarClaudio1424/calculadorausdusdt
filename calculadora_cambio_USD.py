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
    from config import GOOGLE_CREDS, SPREADSHEET_ID, SHEET_TAB_NAME, DROPBOX_ACCESS_TOKEN
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
    """Conecta a Dropbox usando el token."""
    try:
        token = st.secrets["DROPBOX_ACCESS_TOKEN"]
    except (FileNotFoundError, KeyError):
        token = "sl.u.AF8N4bLyY9QrJHrkOkDXyr30YFW99qHzXquitbSVZReEiAuRpvlIQvFBf_ydOJiWEW6n37qJHN8mdHSZUzt5_9ZcrfwXYWY5qy9w-QPgcevyPAXaC9HXcUOLMajBC89o3k6uv5SPNZ5TuiLMUlIal4C9YJxcsentsTd1DR1c2Zh9WXEbVIe4-0UK7e3az4Mb-EnYkIVRhcHJdONuWl6JRO7gsvJds9_U5uKPs8T2hoiOrKDyeP_jscttFUuec5oFaorDAk2oNmVk0wY26gXb_WkNKiL6tEaKGqRrP75MCdy7Sb-uAreQGfQzl637hvfMPzcMXof0sxJSDd-UmtNFW-NI7vaLT9JrWwLOTBKjmZ2KmIna7vVB6RPzrU_snCPNw17LyzcVSIyWK_1UO2uMJSxFojkAwf8dsfTwsosTlNXWAY4uKRTOl8EcLUtXnbvrZAiPeIh7ZkFDTbzqrYc_ol0gzoqaGVGu1k9uk_Bq7U7Z1JH0OCYgkbb_tDcu_W82fXhCK9R-XfVHmW3BFhKgB5MJu2-ArJuQmsMJOnsQnSZQzFi5MI4yPU4NYu90MfHsNC6S-NDt3_DtbUdJRM4m00hY30f5uaurlaxHj4HvzZDLdHlBVnrwL3vS2sgZlYlwf4w-CVqjbGPrGujxzMTseSmXC_dWn8oZ9Gok84bDRip82AhgFKWafwl9r1aJJlsZx50RYhfspkV_ysMDjSDfgjZyV4_3TWW361q11m2Ul3Jm1e-NOeWK0NSOGIU6zCx-F-wT6jW6t6wlUEkfvJovltyQE56coD3PGravIQv3RtbEyDBttBI8b2opr8BDz1XuGhyZhpJNR7xZ54H8NKnxUDWHaipVNDpVVYSKm6byY9cpwA4DkJSNJF03y_-xj8-RJlB0701qVyzs1t4xMl1BoJPIgX3AStzCaQHbCGW4XAyLNJoIeIhsnAMmhsMzg80pZnCvlVhZX-anSBgadFrSsg8Bm60TxyTPi6lp0HHtN-adO2m5tKEjfYtoQlCZ6p9c0E-rfHC3ct76urrhzdMJcKQtltf10iDxJIdY_7MnRE3a_SQEEIbHOXOaZ0ktkG__jQ4xB5ew_GcfSQdjQOY27zunSsbRMcOgHkfLBqs-UT9oVKxcnyIKrRzjEgWeCSLuVQOXQtY-r2Xf-wIFR2Kn3-Do8gK63_aRW7eucVd3-wL5KuhOJORAVFCCpY0AJ_oYGwcAEicjDo9fBlmtbTA6JSu4_JMkqM12CRlUGQ7TTIrfTxDEUJdgA9u1V3lDKl2FTTtR02tyb6vJzK7XOFDJkYc42yVyDVO6PAncp6nBCs96K1inSPCrQyRkRG3HbAfsi-FFHEWaeXLd_sz8rpZjNAPkZwxiiQyfjjjhW_XiLYcXM3gRPoqSgMttHM6BbxDv3M-97FRJ5tkDZwcN3c0pXtVLcPKVf6xIiXpHeIK1_hqnZz5vA37q-lQIUZum27hDJpozB259T5dp7SJijfOh3YuK"
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

def create_calculation_row(row_index, comision_compra, comision_venta, mode_compra, mode_venta):
    div_height = 78 if row_index == 0 else 38
    col_compra, _, col_venta = st.columns([1, 0.2, 1])

    usd_compra_final, usdt_compra_final, input_compra = 0.0, 0.0, 0.0
    usd_venta_final, usdt_venta_final, input_venta = 0.0, 0.0, 0.0

    with col_compra:
        if row_index == 0: st.subheader("Compra (Tú das USD)")
        label_visibility = "visible" if row_index == 0 else "collapsed"
        
        if mode_compra == "USD ➔ USDT":
            input_label = "Monto en USD que das"
            input_compra = st.number_input(input_label, min_value=0.0, format="%.2f", step=100.0, key=f"input_compra_{row_index}", label_visibility=label_visibility)
            usd_compra_final = input_compra
            usdt_compra_final = usd_compra_final * (1 - comision_compra / 100)
            resultado_texto = f"<h6>USDT que recibes:</h6><p style='font-size: 28px; font-weight: bold; color: #228B22; margin: 0;'>{usdt_compra_final:,.2f} USDT</p>"
        else: # USDT ➔ USD
            input_label = "Monto en USDT a recibir"
            input_compra = st.number_input(input_label, min_value=0.0, format="%.2f", step=100.0, key=f"input_compra_{row_index}", label_visibility=label_visibility)
            usdt_compra_final = input_compra
            usd_compra_final = usdt_compra_final / (1 - comision_compra / 100) if comision_compra < 100 else 0
            resultado_texto = f"<h6>USD que das:</h6><p style='font-size: 28px; font-weight: bold; color: #DC143C; margin: 0;'>{usd_compra_final:,.2f} USD</p>"

        res_col, up_col = st.columns([0.7, 0.3])
        with res_col:
            st.markdown(f"""<div style="height: {div_height-3}px;">{resultado_texto}</div>""", unsafe_allow_html=True)
        with up_col:
            st.file_uploader("Comp.", type=["png", "jpg", "jpeg", "pdf"], key=f"uploader_compra_{row_index}", label_visibility="collapsed")

    with col_venta:
        if row_index == 0: st.subheader("Venta (Tú recibes USD)")
        label_visibility = "visible" if row_index == 0 else "collapsed"

        if mode_venta == "USD ➔ USDT":
            input_label = "Monto en USD que recibes"
            input_venta = st.number_input(input_label, min_value=0.0, format="%.2f", step=100.0, key=f"input_venta_{row_index}", label_visibility=label_visibility)
            usd_venta_final = input_venta
            usdt_venta_final = usd_venta_final * (1 - comision_venta / 100)
            resultado_texto = f"<h6>USDT que das:</h6><p style='font-size: 28px; font-weight: bold; color: #DC143C; margin: 0;'>{usdt_venta_final:,.2f} USDT</p>"
        else: # USDT ➔ USD
            input_label = "Monto en USDT a dar"
            input_venta = st.number_input(input_label, min_value=0.0, format="%.2f", step=100.0, key=f"input_venta_{row_index}", label_visibility=label_visibility)
            usdt_venta_final = input_venta
            usd_venta_final = usdt_venta_final / (1 - comision_venta / 100) if comision_venta < 100 else 0
            resultado_texto = f"<h6>USD que recibes:</h6><p style='font-size: 28px; font-weight: bold; color: #228B22; margin: 0;'>{usd_venta_final:,.2f} USD</p>"

        res_col, up_col = st.columns([0.7, 0.3])
        with res_col:
            st.markdown(f"""<div style="height: {div_height-3}px;">{resultado_texto}</div>""", unsafe_allow_html=True)
        with up_col:
            st.file_uploader("Comp.", type=["png", "jpg", "jpeg", "pdf"], key=f"uploader_venta_{row_index}", label_visibility="collapsed")
        
    return {
        "usd_dados_compra": usd_compra_final if input_compra > 0 else 0,
        "usdt_recibidos_compra": usdt_compra_final if input_compra > 0 else 0,
        "usd_recibidos_venta": usd_venta_final if input_venta > 0 else 0,
        "usdt_dados_venta": usdt_venta_final if input_venta > 0 else 0
    }

def create_ajuste_row(row_index):
    col_pago, _, col_recibo = st.columns([1, 0.2, 1])
    if row_index == 0:
        with col_pago: st.subheader("Pagos (Salidas)")
        with col_recibo: st.subheader("Recibos (Entradas)")
    
    with col_pago:
        label_visibility = "visible" if row_index == 0 else "collapsed"
        in_col, up_col = st.columns([0.7, 0.3])
        with in_col:
            pago_monto = st.number_input("Monto del Pago", min_value=0.0, format="%.2f", key=f"pago_monto_{row_index}", label_visibility=label_visibility)
        with up_col:
            st.file_uploader("Comp. Pago", type=["png", "jpg", "jpeg", "pdf"], key=f"uploader_pago_{row_index}", label_visibility="collapsed")

    with col_recibo:
        label_visibility = "visible" if row_index == 0 else "collapsed"
        in_col, up_col = st.columns([0.7, 0.3])
        with in_col:
            recibo_monto = st.number_input("Monto del Recibo", min_value=0.0, format="%.2f", key=f"recibo_monto_{row_index}", label_visibility=label_visibility)
        with up_col:
            st.file_uploader("Comp. Recibo", type=["png", "jpg", "jpeg", "pdf"], key=f"uploader_recibo_{row_index}", label_visibility="collapsed")
            
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
    st.markdown("<h1 style='text-align: center;'>Calculadora y Registro de Operaciones 🏦</h1>", unsafe_allow_html=True)
    st.markdown("---")
    gsheet_client, SPREADSHEET_ID, SHEET_TAB_NAME = connect_to_google_sheets()
    dbx_client = connect_to_dropbox()

    def add_calculo_row(): st.session_state.num_rows = st.session_state.get('num_rows', 1) + 1
    def add_ajuste_row(): st.session_state.num_ajustes = st.session_state.get('num_ajustes', 1) + 1
    def limpiar_calculos_callback():
        for i in range(st.session_state.get('num_rows', 1)):
            if f"input_compra_{i}" in st.session_state: st.session_state[f"input_compra_{i}"] = 0.0
            if f"input_venta_{i}" in st.session_state: st.session_state[f"input_venta_{i}"] = 0.0
        st.session_state.num_rows = 1
    def limpiar_ajustes_callback():
        for i in range(st.session_state.get('num_ajustes', 1)):
            if f"pago_monto_{i}" in st.session_state: st.session_state[f"pago_monto_{i}"] = 0.0
            if f"recibo_monto_{i}" in st.session_state: st.session_state[f"recibo_monto_{i}"] = 0.0
        st.session_state.num_ajustes = 1
    def limpiar_todo_callback():
        limpiar_calculos_callback(); limpiar_ajustes_callback()
        if "cliente_selector" in st.session_state: st.session_state.cliente_selector = "-- Seleccione un Cliente --"

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
    # <-- LÓGICA DE AJUSTE CORREGIDA
    with col_t1: st.metric("TOTAL USDT RECIBIDOS (Op. + Ajustes)", f"{total_usdt_recibidos_op + total_usdt_pagos_ajuste:,.2f} USDT")
    with col_t2: st.metric("TOTAL USDT ENTREGADOS (Op. + Ajustes)", f"{total_usdt_entregados_op + total_usdt_recibos_ajuste:,.2f} USDT")
    st.subheader("Balance Final de Cierre del Cliente ⚖️")
    # <-- LÓGICA DE AJUSTE CORREGIDA
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
                for i, row in enumerate(all_rows_data):
                    if row['usd_dados_compra'] > 0:
                        operations_to_process.append({'type': 'Compra', 'index': i, 'data': row})
                    if row['usd_recibidos_venta'] > 0:
                        operations_to_process.append({'type': 'Venta', 'index': i, 'data': row})
                for i, row in enumerate(all_ajustes_data):
                    if row['pago_usdt'] > 0: operations_to_process.append({'type': 'Ajuste-Pago', 'index': i, 'data': row})
                    if row['recibo_usdt'] > 0: operations_to_process.append({'type': 'Ajuste-Recibo', 'index': i, 'data': row})
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
                        link = ""
                        if op['type'] == 'Compra':
                            uploader_key = f"uploader_compra_{op['index']}"
                            if uploader_key in st.session_state and st.session_state.get(uploader_key):
                                link = upload_to_dropbox(dbx_client, st.session_state[uploader_key], selected_client_name)
                            data_to_save_batch.append([current_folio, timestamp, selected_client_name, "Compra (Das USD)", op['data']['usd_dados_compra'], op['data']['usdt_recibidos_compra'], comision_compra, link])
                        elif op['type'] == 'Venta':
                            uploader_key = f"uploader_venta_{op['index']}"
                            if uploader_key in st.session_state and st.session_state.get(uploader_key):
                                link = upload_to_dropbox(dbx_client, st.session_state[uploader_key], selected_client_name)
                            data_to_save_batch.append([current_folio, timestamp, selected_client_name, "Venta (Recibes USD)", op['data']['usd_recibidos_venta'], op['data']['usdt_dados_venta'], comision_venta, link])
                        elif op['type'] == 'Ajuste-Pago':
                            uploader_key = f"uploader_pago_{op['index']}"
                            if uploader_key in st.session_state and st.session_state.get(uploader_key):
                                link = upload_to_dropbox(dbx_client, st.session_state[uploader_key], selected_client_name)
                            data_to_save_batch.append([current_folio, timestamp, selected_client_name, "Ajuste: Pago Cliente", "", op['data']['pago_usdt'], "N/A", link])
                        elif op['type'] == 'Ajuste-Recibo':
                            uploader_key = f"uploader_recibo_{op['index']}"
                            if uploader_key in st.session_state and st.session_state.get(uploader_key):
                                link = upload_to_dropbox(dbx_client, st.session_state[uploader_key], selected_client_name)
                            data_to_save_batch.append([current_folio, timestamp, selected_client_name, "Ajuste: Recibo Tuyo", "", op['data']['recibo_usdt'], "N/A", link])
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
        st.button("🔄 Limpiar Todo", use_container_width=True, on_click=limpiar_todo_callback)

if __name__ == "__main__":
    main()