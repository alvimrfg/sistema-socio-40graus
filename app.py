# app.py
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta
import database as db
import auth

# Importa as "páginas"
from views import gestao_acesso
from views import clientes_cotas
# from views import reservas_calendario # Descomente quando o arquivo for criado

# --- INICIALIZAÇÃO DO BANCO DE DADOS ---
# Esta é a linha que faltava. Ela garante que o BD e as tabelas existam.
db.init_db()

# --- Configuração da Página ---
st.set_page_config(page_title="Sócio 40 Graus", layout="wide")

# --- Estado da Sessão ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'page' not in st.session_state: st.session_state['page'] = 'dashboard'

# =================================================================================
# ROTEADOR PRINCIPAL DA APLICAÇÃO
# =================================================================================

if not st.session_state.get('logged_in'):
    # Lógica de Login (sem alterações)
    st.header("Login - Sistema Sócio 40 Graus")
    with st.form("login_form"):
        username = st.text_input("Usuário").lower()
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        if submitted:
            @st.cache_data(ttl=300)
            def get_user_data(username):
                with sqlite3.connect(db.DB_FILE) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                    data = cursor.fetchone()
                    return dict(data) if data else None
            user_data = get_user_data(username)
            if user_data and auth.verify_password(password, user_data['password_hash']):
                st.session_state['logged_in'] = True
                st.session_state['username'] = user_data['username']
                st.session_state['user_role'] = user_data['role']
                st.session_state['page'] = 'dashboard'
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
else:
    # BARRA LATERAL DE NAVEGAÇÃO (sem alterações)
    with st.sidebar:
        st.title(f"Bem-vindo(a),\n{st.session_state['username'].capitalize()}!")
        st.markdown(f"**Função:** `{st.session_state['user_role']}`")
        st.divider()
        st.header("Menu Principal")
        if st.button("Dashboard", use_container_width=True):
            st.session_state.page = 'dashboard'
            st.rerun()
        if st.button("Clientes e Cotas", use_container_width=True):
            st.session_state.page = 'clientes_cotas'
            st.rerun()
        # if st.button("Reservas e Calendário", use_container_width=True):
        #     st.session_state.page = 'reservas_calendario'
        #     st.rerun()

        if st.session_state.get('user_role') == 'admin':
            st.divider()
            st.header("Administração")
            if st.button("Gestão de Acesso", use_container_width=True):
                st.session_state.page = 'gestao_acesso'
                st.rerun()
        
        st.divider()
        with st.expander("Alterar Minha Senha"):
             with st.form("change_password_form_sidebar", clear_on_submit=True):
                current_password = st.text_input("Senha Atual", type="password", key="pw_current_sidebar")
                new_password = st.text_input("Nova Senha", type="password", key="pw_new_sidebar")
                confirm_password = st.text_input("Confirmar Nova Senha", type="password", key="pw_confirm_sidebar")
                if st.form_submit_button("Alterar Senha"):
                    # Lógica de alterar senha aqui...
                    pass
        
        if st.button("Logout", use_container_width=True, type="primary"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    # RENDERIZAÇÃO DA PÁGINA SELECIONADA (sem alterações)
    if st.session_state.page == 'dashboard':
        st.title("Dashboard")
        #... (conteúdo do dashboard)
    elif st.session_state.page == 'clientes_cotas':
        clientes_cotas.show_page()
    # elif st.session_state.page == 'reservas_calendario':
    #     reservas_calendario.show_page()
    elif st.session_state.page == 'gestao_acesso':
        gestao_acesso.show_page()