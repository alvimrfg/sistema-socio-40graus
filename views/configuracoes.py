# views/configuracoes.py
import streamlit as st
import database as db
from datetime import date, timedelta

def show_page():
    if st.session_state.get('user_role') != 'admin':
        st.error("Você não tem permissão para acessar esta página.")
        st.stop()

    st.title("⚙️ Configurações do Sistema")
    
    if 'action_success_message' in st.session_state:
        st.success(st.session_state.action_success_message)
        del st.session_state.action_success_message

    st.header("Financeiro")
    with st.form("financial_settings_form"):
        settings = db.get_all_settings()
        st.subheader("Valores das Cotas")
        price_simple = st.number_input("Preço Cota Simples (R$)", value=float(settings.get('simple_quota_price', 1400)), min_value=0.0, format="%.2f")
        price_premium = st.number_input("Preço Cota Premium (R$)", value=float(settings.get('premium_quota_price', 2000)), min_value=0.0, format="%.2f")
        
        st.subheader("Taxas de Feriados Especiais")
        fee_simple = st.number_input("Taxa para Cota Simples (R$ por pessoa)", value=float(settings.get('special_holiday_fee_simple', 200)), min_value=0.0, format="%.2f")
        fee_premium = st.number_input("Taxa para Cota Premium (R$ por pessoa)", value=float(settings.get('special_holiday_fee_premium', 100)), min_value=0.0, format="%.2f")

        submitted_prices = st.form_submit_button("Salvar Configurações Financeiras", use_container_width=True)
        if submitted_prices:
            db.update_setting('simple_quota_price', str(price_simple))
            db.update_setting('premium_quota_price', str(price_premium))
            db.update_setting('special_holiday_fee_simple', str(fee_simple))
            db.update_setting('special_holiday_fee_premium', str(fee_premium))
            st.session_state.action_success_message = "Preços e taxas atualizados com sucesso!"
            st.rerun()

    st.divider()

    st.header("Inventário de Acomodações")
    accommodations = db.get_all_accommodations()
    with st.form("accommodations_form"):
        for index, row in accommodations.iterrows():
            st.number_input(label=f"Quantidade de **{row['type']}**", value=row['total_quantity'], min_value=0, step=1, key=f"qty_{row['type']}")
        submitted_accommodations = st.form_submit_button("Salvar Quantidades", use_container_width=True)
        if submitted_accommodations:
            for index, row in accommodations.iterrows():
                new_quantity = st.session_state[f"qty_{row['type']}"]
                db.update_accommodation_quantity(row['type'], new_quantity)
            st.session_state.action_success_message = "Inventário de acomodações atualizado!"
            st.rerun()

    st.divider()

    st.header("Calendário de Feriados")
    tab1, tab2 = st.tabs(["Visualizar e Remover Feriados", "Adicionar Novo Feriado"])

    with tab1:
        all_holidays = db.get_all_holidays()
        st.dataframe(all_holidays, use_container_width=True, hide_index=True)
        if not all_holidays.empty:
            holiday_options = {f"{row['Nome']} ({row['Início']})": row['id'] for index, row in all_holidays.iterrows()}
            selected_holiday_display = st.selectbox("Selecione um feriado para remover", options=holiday_options.keys())
            if st.button("Remover Feriado Selecionado", type="primary", use_container_width=True):
                holiday_id_to_delete = holiday_options[selected_holiday_display]
                if db.delete_holiday(holiday_id_to_delete):
                    st.session_state.action_success_message = "Feriado removido com sucesso!"
                    st.rerun()
    
    with tab2:
        with st.form("new_holiday_form", clear_on_submit=True):
            name = st.text_input("Nome do Feriado (ex: Páscoa 2026)")
            h_c1, h_c2 = st.columns(2)
            with h_c1: start_date = st.date_input("Data de Início", value=date.today())
            with h_c2: end_date = st.date_input("Data de Fim", value=date.today() + timedelta(days=3))
            holiday_type = st.selectbox("Tipo de Feriado", ["Comum", "Especial"])
            submitted_holiday = st.form_submit_button("Adicionar Feriado", use_container_width=True)
            if submitted_holiday:
                if name and start_date and end_date and holiday_type:
                    if start_date > end_date: st.warning("A data de fim deve ser igual ou posterior à data de início.")
                    else:
                        db.add_holiday(name, start_date.isoformat(), end_date.isoformat(), holiday_type)
                        st.session_state.action_success_message = "Feriado adicionado com sucesso!"
                        st.rerun()