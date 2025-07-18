# views/reservas_calendario.py
import streamlit as st
import database as db
import pandas as pd
from datetime import date, timedelta
from streamlit_calendar import calendar

def show_page():
    st.title("Reservas e Calendário de Ocupação")

    if 'action_success_message' in st.session_state:
        st.success(st.session_state.action_success_message)
        del st.session_state.action_success_message

    # Adicionamos a nova aba 'Gerenciar Reservas'
    tab1, tab2, tab3 = st.tabs(["🗓️ Calendário", "➕ Nova Reserva", "📋 Gerenciar Reservas"])

    with tab1:
        st.header("Ocupação das Acomodações")
        booking_events = db.get_all_bookings_for_calendar()
        calendar(events=booking_events, options={
            "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,timeGridWeek"},
            "initialView": "dayGridMonth", "locale": "pt-br"
        })

    with tab2:
        st.header("Agendar Nova Reserva")
        member_list_df = db.get_all_members()

        if member_list_df.empty:
            st.warning("Nenhum sócio cadastrado. Por favor, cadastre um sócio na página 'Clientes e Cotas' antes de fazer uma reserva.")
        else:
            with st.form("new_booking_form"):
                member_options = {f"{row['Nome Completo']} (ID: {row['ID']})": row['ID'] for index, row in member_list_df.iterrows()}
                selected_member_display = st.selectbox("Selecione um Sócio*", options=member_options.keys(), index=None, placeholder="Escolha um sócio...")
                
                member_id = member_options.get(selected_member_display) if selected_member_display else None
                allowance = db.get_member_allowance(member_id) if member_id else None

                if allowance:
                    st.info(f"Saldo do Sócio: **{allowance['available']}** diárias disponíveis (de um total de {allowance['total']}).", icon="🗓️")

                c1, c2 = st.columns(2)
                with c1: start_date = st.date_input("Data de Check-in*", value=date.today())
                with c2: end_date = st.date_input("Data de Check-out*", value=date.today() + timedelta(days=2))
                
                accommodation_types = db.get_accommodation_types()
                accommodation_type = st.selectbox("Tipo de Acomodação*", options=accommodation_types)
                
                booking_duration = (end_date - start_date).days
                all_validations_passed = False
                
                if selected_member_display:
                    if booking_duration <= 0:
                        st.error("A data de Check-out deve ser posterior à de Check-in.")
                    else:
                        if allowance and allowance['available'] < booking_duration:
                            st.error(f"Saldo insuficiente! O sócio tem {allowance['available']} diárias, mas a reserva requer {booking_duration}.")
                        else:
                            available_units = db.check_availability(accommodation_type, start_date.isoformat(), end_date.isoformat())
                            if available_units <= 0:
                                st.error(f"Indisponível! Todas as unidades de {accommodation_type} já estão reservadas neste período.")
                            else:
                                st.success(f"Pré-reserva válida! A reserva consumirá {booking_duration} diárias e há {available_units} unidade(s) livre(s).")
                                all_validations_passed = True
                
                submitted = st.form_submit_button("Confirmar Reserva", disabled=not all_validations_passed, use_container_width=True)
                if submitted:
                    if not member_id:
                        st.error("Por favor, selecione um sócio.")
                    else:
                        if db.add_booking(member_id, accommodation_type, start_date.isoformat(), end_date.isoformat()):
                            st.session_state.action_success_message = "Reserva confirmada com sucesso!"
                            st.rerun()
                        else:
                            st.error("Ocorreu um erro ao salvar a reserva.")

    # --- NOVA ABA DE GERENCIAMENTO DE RESERVAS ---
    with tab3:
        st.header("Todas as Reservas")
        all_bookings = db.get_all_bookings_with_details()

        if all_bookings.empty:
            st.info("Nenhuma reserva encontrada.")
        else:
            # Filtros
            st.subheader("Filtrar Reservas")
            col1, col2 = st.columns(2)
            with col1:
                filter_name = st.text_input("Filtrar por nome do sócio")
            with col2:
                filter_status = st.selectbox("Filtrar por status", options=["Todos", "Confirmada", "Cancelada", "Pendente"], index=0)

            filtered_df = all_bookings.copy()
            if filter_name:
                filtered_df = filtered_df[filtered_df['Sócio'].str.contains(filter_name, case=False)]
            if filter_status != "Todos":
                filtered_df = filtered_df[filtered_df['Status'] == filter_status]

            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

            st.subheader("Alterar Status de uma Reserva")
            if not filtered_df.empty:
                booking_options = {f"ID {row['ID Reserva']} - {row['Sócio']} ({row['Check-in']})": row['ID Reserva'] for index, row in filtered_df.iterrows()}
                selected_booking_display = st.selectbox("Selecione uma reserva para alterar", options=booking_options.keys())
                
                new_status = st.selectbox("Selecione o novo status", options=["Confirmada", "Cancelada"], key="new_status_select")

                if st.button("Salvar Alteração de Status", type="primary"):
                    booking_id = booking_options[selected_booking_display]
                    if db.update_booking_status(booking_id, new_status):
                        st.session_state.action_success_message = f"Status da reserva ID {booking_id} alterado para '{new_status}' com sucesso!"
                        st.rerun()
                    else:
                        st.error("Falha ao atualizar o status da reserva.")
            else:
                st.info("Nenhum resultado encontrado para os filtros aplicados.")