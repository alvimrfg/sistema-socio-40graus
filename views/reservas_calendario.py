# views/reservas_calendario.py
import streamlit as st
import database as db
from datetime import date, timedelta
from streamlit_calendar import calendar

def show_page():
    st.title("Reservas e Calendário de Ocupação")

    if 'action_success_message' in st.session_state:
        st.success(st.session_state.action_success_message)
        del st.session_state.action_success_message

    tab1, tab2 = st.tabs(["🗓️ Calendário de Reservas", "➕ Fazer Nova Reserva"])

    with tab1:
        st.header("Ocupação das Acomodações")
        booking_events = db.get_all_bookings_for_calendar()
        calendar_options = {
            "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,timeGridWeek"},
            "initialView": "dayGridMonth", "locale": "pt-br"
        }
        calendar(events=booking_events, options=calendar_options, custom_css="""
            .fc-event-past { opacity: 0.8; } .fc-event-time { font-style: italic; }
            .fc-event-title { font-weight: 700; } .fc-toolbar-title { font-size: 1.5rem; }""")

    with tab2:
        st.header("Agendar Nova Reserva")
        with st.form("new_booking_form", clear_on_submit=True):
            member_list_df = db.get_all_members()
            if member_list_df.empty:
                st.warning("Nenhum sócio cadastrado. Por favor, cadastre um sócio na página 'Clientes e Cotas' antes de fazer uma reserva.")
                st.stop()

            member_options = {f"{row['Nome Completo']} (ID: {row['ID']})": row['ID'] for index, row in member_list_df.iterrows()}
            selected_member_display = st.selectbox("Selecione um Sócio*", options=member_options.keys())

            c1, c2 = st.columns(2)
            with c1: start_date = st.date_input("Data de Check-in*", value=date.today())
            with c2: end_date = st.date_input("Data de Check-out*", value=date.today() + timedelta(days=2))

            # CORREÇÃO: Usando a nova função do database.py
            accommodation_types = db.get_accommodation_types()
            accommodation_type = st.selectbox("Tipo de Acomodação*", options=accommodation_types)

            is_available = False
            if start_date >= end_date:
                st.warning("A data de Check-out deve ser posterior à data de Check-in.")
            else:
                available_units = db.check_availability(accommodation_type, start_date.isoformat(), end_date.isoformat())
                if available_units > 0:
                    st.info(f"Disponível! Há {available_units} unidade(s) livre(s) neste período.", icon="✅")
                    is_available = True
                else:
                    st.error(f"Indisponível! Todas as unidades deste tipo já estão reservadas.", icon="❌")
            
            submitted = st.form_submit_button("Confirmar Reserva", disabled=not is_available, use_container_width=True)
            if submitted:
                member_id = member_options[selected_member_display]
                if db.add_booking(member_id, accommodation_type, start_date.isoformat(), end_date.isoformat()):
                    st.session_state.action_success_message = "Reserva confirmada com sucesso!"
                    st.rerun()
                else:
                    st.error("Ocorreu um erro ao salvar a reserva.")