# app.py
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta
import database as db
import auth
from views import gestao_acesso, clientes_cotas, reservas_calendario

st.set_page_config(page_title="Sócio 40 Graus", layout="wide")

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'page' not in st.session_state: st.session_state['page'] = 'dashboard'

if not st.session_state.get('logged_in'):
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
        if st.button("Reservas e Calendário", use_container_width=True):
            st.session_state.page = 'reservas_calendario'
            st.rerun()
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
                    # ... (lógica de alterar senha)
                    pass
        if st.button("Logout", use_container_width=True, type="primary"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    if st.session_state.page == 'dashboard':
        st.title("Dashboard")
        kpis = db.get_dashboard_kpis()
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Total de Cotistas Ativos", value=kpis['total_members'])
        col2.metric(label="Faturamento de Cotas (Pago)", value=f"R$ {kpis['total_revenue']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col3.metric(label="Ocupação (Próx. 30 dias)", value=f"{kpis['occupancy_rate']:.1f}%")
        st.markdown("---")
        col4, col5 = st.columns([0.6, 0.4])
        with col4:
            st.subheader("Distribuição de Cotas")
            member_counts = db.get_members_by_quota_type()
            if not member_counts.empty: st.bar_chart(member_counts.set_index('quota_type'))
            else: st.info("Ainda não há sócios cadastrados.")
        with col5:
            st.subheader(f"Próximos Check-ins (7 dias)")
            upcoming_checkins = db.get_upcoming_checkins(days=7)
            if not upcoming_checkins.empty: st.dataframe(upcoming_checkins, use_container_width=True, hide_index=True)
            else: st.info("Nenhum check-in agendado.")
    elif st.session_state.page == 'clientes_cotas':
        clientes_cotas.show_page()
    elif st.session_state.page == 'reservas_calendario':
        reservas_calendario.show_page()
    elif st.session_state.page == 'gestao_acesso':
        gestao_acesso.show_page()