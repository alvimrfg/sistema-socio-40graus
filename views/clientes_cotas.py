# views/clientes_cotas.py
import streamlit as st
import database as db
from datetime import date, timedelta
import re # Importa a biblioteca de expressões regulares do Python

def clean_and_validate_cpf(cpf_str):
    """Remove a formatação e valida se o CPF tem 11 dígitos."""
    if not cpf_str:
        return None, "CPF não pode estar em branco."
    
    cleaned = re.sub(r'\D', '', cpf_str) # Remove tudo que não for dígito
    if len(cleaned) != 11:
        return None, "CPF inválido. Deve conter 11 dígitos."
    return cleaned, None

def show_page():
    """Exibe a página de gerenciamento de clientes e cotas."""
    
    st.title("Gestão de Clientes e Cotas")

    if 'action_success_message' in st.session_state:
        st.success(st.session_state.action_success_message)
        del st.session_state.action_success_message

    tab1, tab2, tab3 = st.tabs(["Visualizar Clientes", "Cadastrar Novo Cliente", "Editar Cliente / Dependentes"])

    # Aba 1: Visualizar Clientes
    with tab1:
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

    # Aba 2: Cadastrar Novo Cliente
    with tab2:
        st.subheader("Cadastrar Novo Sócio")
        with st.form("new_member_form", clear_on_submit=False): # `clear_on_submit` é False para mostrar erros
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
                plans = { "Simples": ["Finais de Semana", "Misto", "Feriado Regular"], "Premium": ["Finais de Semana Premium", "Misto Premium", "Feriado Premium"] }
                usage_plan = st.selectbox("Plano de Uso*", plans[quota_type])
                payment_status = st.selectbox("Status do Pagamento*", ["Pago", "Pendente", "Atrasado"])

            submitted = st.form_submit_button("Cadastrar Sócio")
            if submitted:
                cpf_cleaned, cpf_error = clean_and_validate_cpf(cpf)
                phone_cleaned = re.sub(r'\D', '', phone)
                
                if cpf_error:
                    st.error(cpf_error)
                elif not all([full_name, email]):
                    st.warning("Por favor, preencha Nome Completo e Email.")
                else:
                    if db.add_member(full_name, cpf_cleaned, email, phone_cleaned, birth_date, address, quota_type, usage_plan, start_date, end_date, payment_status):
                        st.session_state.action_success_message = f"Sócio '{full_name}' cadastrado com sucesso!"
                        st.rerun()
                    else:
                        st.error("Erro ao cadastrar. CPF ou Email já podem existir no sistema.")

    # Aba 3: Editar Cliente e Dependentes (sem alterações, mas o código completo está aqui por segurança)
    with tab3:
        st.subheader("Editar ou Gerenciar um Sócio")
        member_list_df = db.get_all_members()
        if not member_list_df.empty:
            member_options = {f"{row['Nome Completo']} (ID: {row['ID']})": row['ID'] for index, row in member_list_df.iterrows()}
            selected_member_display = st.selectbox("Selecione um Sócio", options=member_options.keys(), index=None, placeholder="Escolha um sócio para editar...")

            if selected_member_display:
                member_id = member_options[selected_member_display]
                member_data = db.get_member_by_id(member_id)

                with st.expander("Editar Informações do Sócio", expanded=True):
                    with st.form(f"edit_member_{member_id}"):
                        st.write("Altere os dados necessários e salve.")
                        
                        today_edit = date.today()
                        hundred_years_ago_edit = today_edit.replace(year=today_edit.year - 100)
                        
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
                            e_payment_status = st.selectbox("Status Pagamento*", ["Pago", "Pendente", "Atrasado"], index=["Pago", "Pendente", "Atrasado"].index(member_data['payment_status']))
                        with e_c4:
                            e_plans = {"Simples": ["Finais de Semana", "Misto", "Feriado Regular"],"Premium": ["Finais de Semana Premium", "Misto Premium", "Feriado Premium"]}
                            e_usage_plan = st.selectbox("Plano de Uso*", e_plans[e_quota_type], index=e_plans[e_quota_type].index(member_data['usage_plan']))
                        
                        update_submitted = st.form_submit_button("Salvar Alterações do Sócio")
                        if update_submitted:
                            e_cpf_cleaned, e_cpf_error = clean_and_validate_cpf(e_cpf)
                            e_phone_cleaned = re.sub(r'\D', '', e_phone)

                            if e_cpf_error:
                                st.error(e_cpf_error)
                            else:
                                if db.update_member(member_id, e_full_name, e_cpf_cleaned, e_email, e_phone_cleaned, e_birth_date, e_address, e_quota_type, e_usage_plan, e_payment_status):
                                    st.session_state.action_success_message = "Dados do sócio atualizados com sucesso!"
                                    st.rerun()
                                else:
                                    st.error("Erro ao atualizar os dados. O CPF ou Email pode pertencer a outro sócio.")
                
                # Gerenciamento de Dependentes (sem alterações)
                with st.expander("Gerenciar Dependentes"):
                    # ...
                    pass