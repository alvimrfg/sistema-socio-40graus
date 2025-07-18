# views/clientes_cotas.py
import streamlit as st
import database as db
from datetime import date, timedelta
import re

def clean_and_validate_cpf(cpf_str):
    if not cpf_str: return None, "CPF não pode estar em branco."
    cleaned = re.sub(r'\D', '', cpf_str)
    if len(cleaned) != 11: return None, "CPF inválido. Deve conter 11 dígitos."
    return cleaned, None

def show_page():
    st.title("Gestão de Clientes e Cotas")

    if 'action_success_message' in st.session_state:
        st.success(st.session_state.action_success_message)
        del st.session_state.action_success_message

    tab1, tab2, tab3 = st.tabs(["Visualizar Clientes", "Cadastrar Novo Cliente", "Editar Cliente / Finanças"])

    with tab1:
        # (código da aba 1, sem alterações)
        st.subheader("Lista de Sócios Ativos")
        search_term = st.text_input("Buscar por nome ou CPF")
        all_members = db.get_all_members()
        if search_term:
            search_digits = re.sub(r'\D', '', search_term)
            all_members = all_members[
                all_members['Nome Completo'].str.contains(search_term, case=False) |
                all_members['CPF'].str.contains(search_digits, case=False)
            ]
        st.dataframe(all_members, use_container_width=True, hide_index=True)

    with tab2:
        # (código da aba 2, sem alterações)
        st.subheader("Cadastrar Novo Sócio")
        with st.form("new_member_form", clear_on_submit=False):
            st.write("Preencha os dados do novo sócio:")
            today = date.today()
            hundred_years_ago = today.replace(year=today.year - 100)
            c1, c2 = st.columns(2)
            with c1:
                full_name = st.text_input("Nome Completo*")
                cpf = st.text_input("CPF*", placeholder="000.000.000-00")
                birth_date = st.date_input("Data de Nascimento", value=None, min_value=hundred_years_ago, max_value=today)
            with c2:
                email = st.text_input("Email*")
                phone = st.text_input("Telefone", placeholder="(00) 00000-0000")
                address = st.text_area("Endereço")
            st.divider()
            st.write("Detalhes da Cota:")
            c3, c4 = st.columns(2)
            with c3:
                quota_type = st.selectbox("Tipo de Cota*", ["Simples", "Premium"])
                start_date = st.date_input("Início da Validade da Cota*", value=today)
                end_date = start_date + timedelta(days=365)
                st.date_input("Fim da Validade", value=end_date, disabled=True)
            with c4:
                plans = {"Simples": ["Finais de Semana", "Misto", "Feriado Regular"], "Premium": ["Finais de Semana Premium", "Misto Premium", "Feriado Premium"]}
                usage_plan = st.selectbox("Plano de Uso*", plans[quota_type])
                payment_status = st.selectbox("Status do Pagamento*", ["Pendente", "Pago", "Atrasado"])
            submitted = st.form_submit_button("Cadastrar Sócio")
            if submitted:
                cpf_cleaned, cpf_error = clean_and_validate_cpf(cpf)
                phone_cleaned = re.sub(r'\D', '', phone)
                if cpf_error: st.error(cpf_error)
                elif not all([full_name, email]): st.warning("Por favor, preencha Nome Completo e Email.")
                else:
                    if db.add_member(full_name, cpf_cleaned, email, phone_cleaned, birth_date, address, quota_type, usage_plan, start_date, end_date, payment_status):
                        st.session_state.action_success_message = f"Sócio '{full_name}' cadastrado com sucesso!"
                        st.rerun()
                    else: st.error("Erro ao cadastrar. CPF ou Email já podem existir no sistema.")

    with tab3:
        # --- LÓGICA DA ABA 3 ATUALIZADA ---
        st.subheader("Editar ou Gerenciar um Sócio")
        member_list_df = db.get_all_members()
        if not member_list_df.empty:
            member_options = {f"{row['Nome Completo']} (ID: {row['ID']})": row['ID'] for index, row in member_list_df.iterrows()}
            selected_member_display = st.selectbox("Selecione um Sócio", options=member_options.keys(), index=None, placeholder="Escolha um sócio para gerenciar...")

            if selected_member_display:
                member_id = member_options[selected_member_display]
                member_data = db.get_member_by_id(member_id)

                with st.expander("Editar Informações do Sócio", expanded=True):
                    # (código de edição, sem alterações)
                    with st.form(f"edit_member_{member_id}"):
                        st.write("Altere os dados necessários e salve.")
                        today_edit, hundred_years_ago_edit = date.today(), date.today().replace(year=date.today().year - 100)
                        e_c1, e_c2 = st.columns(2)
                        with e_c1:
                            e_full_name = st.text_input("Nome Completo*", value=member_data['full_name'])
                            e_cpf = st.text_input("CPF*", value=member_data['cpf'])
                            e_birth_date_val = date.fromisoformat(member_data['birth_date']) if member_data['birth_date'] else None
                            e_birth_date = st.date_input("Data de Nascimento", value=e_birth_date_val, min_value=hundred_years_ago_edit, max_value=today_edit)
                        with e_c2:
                            e_email = st.text_input("Email*", value=member_data['email'])
                            e_phone = st.text_input("Telefone", value=member_data['phone'])
                            e_address = st.text_area("Endereço", value=member_data['address'])
                        e_c3, e_c4 = st.columns(2)
                        with e_c3:
                            e_quota_type = st.selectbox("Tipo de Cota*", ["Simples", "Premium"], index=["Simples", "Premium"].index(member_data['quota_type']))
                            e_payment_status = st.selectbox("Status Pagamento*", ["Pendente", "Pago", "Atrasado"], index=["Pendente", "Pago", "Atrasado"].index(member_data['payment_status']))
                        with e_c4:
                            e_plans = {"Simples": ["Finais de Semana", "Misto", "Feriado Regular"],"Premium": ["Finais de Semana Premium", "Misto Premium", "Feriado Premium"]}
                            e_usage_plan = st.selectbox("Plano de Uso*", e_plans[e_quota_type], index=e_plans[e_quota_type].index(member_data['usage_plan']))
                        update_submitted = st.form_submit_button("Salvar Alterações do Sócio")
                        if update_submitted:
                            e_cpf_cleaned, e_cpf_error = clean_and_validate_cpf(e_cpf)
                            e_phone_cleaned = re.sub(r'\D', '', e_phone)
                            if e_cpf_error: st.error(e_cpf_error)
                            else:
                                if db.update_member(member_id, e_full_name, e_cpf_cleaned, e_email, e_phone_cleaned, e_birth_date, e_address, e_quota_type, e_usage_plan, e_payment_status):
                                    st.session_state.action_success_message = "Dados do sócio atualizados com sucesso!"
                                    st.rerun()
                                else: st.error("Erro ao atualizar. O CPF ou Email pode pertencer a outro sócio.")
                
                with st.expander("Gerenciar Dependentes"):
                    # (código de dependentes, sem alterações)
                    dependents_df = db.get_dependents(member_id)
                    st.write(f"Atualmente com {len(dependents_df)} de 3 dependentes.")
                    if not dependents_df.empty: st.dataframe(dependents_df, use_container_width=True, hide_index=True)
                    if len(dependents_df) < 3:
                        with st.form(f"add_dependent_{member_id}", clear_on_submit=True):
                            new_dependent_name = st.text_input("Nome do Novo Dependente")
                            if st.form_submit_button("Adicionar Dependente") and new_dependent_name:
                                if db.add_dependent(member_id, new_dependent_name): st.session_state.action_success_message = "Dependente adicionado!"; st.rerun()
                    else: st.info("Limite de 3 dependentes atingido.")
                    if not dependents_df.empty:
                        dep_to_delete_options = {row['Nome Completo']: row['id'] for index, row in dependents_df.iterrows()}
                        dep_to_delete_name = st.selectbox("Selecione o dependente a remover", options=dep_to_delete_options.keys())
                        if st.button("Remover Dependente Selecionado", type="primary"):
                            dependent_id = dep_to_delete_options[dep_to_delete_name]
                            if db.delete_dependent(dependent_id): st.session_state.action_success_message = "Dependente removido!"; st.rerun()
                
                # --- NOVA SEÇÃO FINANCEIRA ADICIONADA AQUI ---
                with st.expander("Histórico Financeiro e Lançamentos"):
                    st.subheader("Histórico de Transações")
                    transactions_df = db.get_transactions_for_member(member_id)
                    st.dataframe(transactions_df, use_container_width=True)
                    
                    total_paid = transactions_df['Valor'].sum()
                    st.metric("Total Pago pelo Sócio", f"R$ {total_paid:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

                    st.subheader("Lançar Novo Pagamento")
                    with st.form(f"new_transaction_{member_id}", clear_on_submit=True):
                        c1, c2 = st.columns(2)
                        with c1:
                            amount = st.number_input("Valor (R$)*", min_value=0.01, format="%.2f")
                            transaction_date = st.date_input("Data do Pagamento*", value=date.today())
                        with c2:
                            description = st.text_area("Descrição*", placeholder="Ex: Pagamento Cota Simples 2026, Taxa Feriado Natal, etc.")
                        
                        # Opção para atualizar o status geral do sócio
                        update_status = st.checkbox("Atualizar status geral do sócio para 'Pago' com este lançamento?")

                        transaction_submitted = st.form_submit_button("Lançar Pagamento")
                        if transaction_submitted:
                            if db.add_transaction(member_id, amount, description, transaction_date.isoformat()):
                                if update_status:
                                    db.update_member_payment_status(member_id, 'Pago')
                                st.session_state.action_success_message = "Lançamento financeiro registrado com sucesso!"
                                st.rerun()
                            else:
                                st.error("Erro ao registrar o lançamento.")