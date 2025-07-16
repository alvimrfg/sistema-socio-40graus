# create_first_admin.py

import database
import auth
import sqlite3

def setup_initial_user():
    """Inicializa o BD e cria o primeiro usuário admin se não houver nenhum."""
    print("Inicializando banco de dados...")
    database.init_db()
    print("Banco de dados pronto.")

    try:
        with sqlite3.connect(database.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]

            if user_count == 0:
                print("Nenhum usuário encontrado. Criando usuário 'admin' padrão...")
                username = "admin"
                password = "admin_password" # Mude isso em um cenário real
                hashed_password = auth.hash_password(password)
                
                # Adiciona o usuário com a função 'admin'
                cursor.execute(
                    "INSERT INTO users (username, password_hash, first_name, last_name, email, role) VALUES (?, ?, ?, ?, ?, ?)",
                    (username, hashed_password, 'Admin', 'User', 'admin@40graus.com', 'admin')
                )
                conn.commit()
                print(f"Usuário '{username}' criado com sucesso com a função de 'admin'.")
                print(f"Senha: '{password}'")
            else:
                print("Usuários já existem no banco de dados. Nenhum usuário foi criado.")
    except sqlite3.Error as e:
        print(f"Erro de banco de dados: {e}")

if __name__ == "__main__":
    setup_initial_user()