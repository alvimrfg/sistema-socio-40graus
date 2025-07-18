# views/gestao_acesso.py
import streamlit as st
import pandas as pd
import auth
import database as db

def show_page():
    if st.session_state.get('user_role') != 'admin':
        st.error("Você não tem permissão para acessar esta página.")
        st.image("https://media1.tenor.com/m/dsw_z2v3jOEAAAAC/gandalf-you-shall-not-pass.gif", width=300)
        st.stop()

    st.title("Gestão de Acesso ao Sistema")
    st.markdown("Crie, edite e remova os usuários que podem fazer login no sistema.")

    if 'action_success_message' in st.session_state:
        st.success(st.session_state.action_success_message)
        del st.session_state.action_success_message

    tab1, tab2, tab3 = st.tabs(["Visualizar Usuários", "Criar Novo Usuário", "Editar / Remover Usuário"])

    with tab1:
        st.subheader("Usuários Cadastrados no Sistema")
        st.dataframe(db.get_system_users(), use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Criar Novo Usuário do Sistema")
        with st.form("create_user_form", clear_on_submit=True):
            st.write("Preencha os dados para criar um novo acesso.")
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("Primeiro Nome")
                username = st.text_input("Nome de Usuário (para login)").lower()
                role = st.selectbox("Função", ["recepcionista", "admin"])
            with col2:
                last_name = st.text_input("Sobrenome")
                email = st.text_input("Email")
                password = st.text_input("Senha Provisória", type="password")
            
            create_submitted = st.form_submit_button("Criar Usuário")
            if create_submitted:
                if not all([first_name, username, role, last_name, email, password]):
                    st.warning("Por favor, preencha todos os campos.")
                else:
                    hashed_password = auth.hash_password(password)
                    if db.add_system_user(username, hashed_password, first_name, last_name, email, role):
                        st.session_state.action_success_message = f"Usuário '{username}' criado com sucesso!"
                        st.rerun()
                    else: st.error("Erro ao criar usuário. O nome de usuário ou email já pode existir.")

    with tab3:
        st.subheader("Editar ou Remover um Usuário Existente")
        users_df_edit = db.get_system_users()
        user_list = users_df_edit['username'].tolist()
        
        selected_user = st.selectbox("Primeiro, selecione um usuário", options=user_list, index=None, placeholder="Escolha um usuário...")

        if selected_user:
            st.markdown("---")
            action = st.radio(f"O que você deseja fazer com **{selected_user}**?",
                              ["Editar Informações", "Remover Usuário"], horizontal=True, key=f"action_{selected_user}")
            
            user_data = users_df_edit[users_df_edit['username'] == selected_user].iloc[0]

            if action == "Editar Informações":
                with st.form(f"edit_{selected_user}"):
                    st.write(f"Editando o usuário ID: **{user_data['id']}**")
                    edit_first_name = st.text_input("Primeiro Nome", value=user_data['first_name'])
                    edit_last_name = st.text_input("Sobrenome", value=user_data['last_name'])
                    edit_email = st.text_input("Email", value=user_data['email'])
                    edit_role = st.selectbox("Função", ["recepcionista", "admin"], index=["recepcionista", "admin"].index(user_data['role']))
                    
                    update_submitted = st.form_submit_button("Salvar Alterações")
                    if update_submitted:
                        user_id = int(user_data['id'])
                        if db.update_system_user(user_id, edit_first_name, edit_last_name, edit_email, edit_role):
                            st.session_state.action_success_message = f"Usuário '{selected_user}' atualizado com sucesso!"
                            st.rerun()
                        else: st.error("Falha ao atualizar o usuário.")
            
            elif action == "Remover Usuário":
                logged_in_user = st.session_state.get('username', '')
                if selected_user not in ['admin', logged_in_user]:
                    st.warning(f"Atenção: Esta ação é irreversível e removerá permanentemente o acesso de **{selected_user}**.", icon="⚠️")
                    if st.button(f"Confirmar Remoção de {selected_user}", type="primary"):
                        user_id = int(user_data['id'])
                        if db.delete_system_user(user_id):
                            st.session_state.action_success_message = f"Usuário '{selected_user}' removido com sucesso."
                            st.rerun()
                        else: st.error("Falha ao remover o usuário.")
                else:
                    st.error(f"O usuário '{selected_user}' não pode ser removido (usuário 'admin' principal ou você mesmo).", icon="🚫")