# database.py
import sqlite3
import pandas as pd
from datetime import date, timedelta

DB_FILE = "socio40graus.db"

# Mapeamento de planos para dias de direito. Centralizado para fácil manutenção.
PLAN_ALLOWANCE_DAYS = {
    "Finais de Semana": 8, "Misto": 8, "Feriado Regular": 8,
    "Finais de Semana Premium": 8, "Misto Premium": 8, "Feriado Premium": 7
}

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Tabela de usuários do sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
                first_name TEXT, last_name TEXT, email TEXT UNIQUE,
                role TEXT NOT NULL DEFAULT 'recepcionista' CHECK(role IN ('admin', 'recepcionista'))
            )""")
        # Tabela de membros com NOVAS COLUNAS para controle de diárias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL, cpf TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL,
                phone TEXT, birth_date DATE, address TEXT, quota_type TEXT NOT NULL CHECK(quota_type IN ('Simples', 'Premium')),
                usage_plan TEXT NOT NULL, 
                allowance_days INTEGER NOT NULL DEFAULT 0,
                used_days INTEGER NOT NULL DEFAULT 0,
                start_date DATE NOT NULL, end_date DATE NOT NULL,
                payment_status TEXT DEFAULT 'Pendente' CHECK(payment_status IN ('Pago', 'Pendente', 'Atrasado')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
        # Tabela de dependentes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dependents (
                id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER NOT NULL, full_name TEXT NOT NULL,
                FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE
            )""")
        # Tabela de acomodações
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accommodations (
                id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT UNIQUE NOT NULL, total_quantity INTEGER NOT NULL
            )""")
        # Tabela de reservas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER NOT NULL, accommodation_type TEXT NOT NULL,
                start_date DATE NOT NULL, end_date DATE NOT NULL,
                status TEXT DEFAULT 'Pendente' CHECK(status IN ('Confirmada', 'Pendente', 'Cancelada')),
                booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES members (id), FOREIGN KEY (accommodation_type) REFERENCES accommodations (type)
            )""")
        # Tabela de feriados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holidays (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, start_date DATE NOT NULL, end_date DATE NOT NULL,
                type TEXT DEFAULT 'Comum' CHECK(type IN ('Especial', 'Comum'))
            )""")
        # Tabela de transações
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER, amount REAL NOT NULL, description TEXT, transaction_date DATE NOT NULL,
                FOREIGN KEY (member_id) REFERENCES members (id)
            )""")
        # Tabela de configurações
        cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.commit()
        populate_initial_data(cursor)
        conn.commit()

def populate_initial_data(cursor):
    settings_to_add = [('simple_quota_price', '1400.00'), ('premium_quota_price', '2000.00'),
                       ('special_holiday_fee_simple', '200.00'), ('special_holiday_fee_premium', '100.00')]
    cursor.executemany("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", settings_to_add)
    accommodations_to_add = [('Quitinete Premium', 2), ('Suíte Média', 1), ('Suíte Pequena', 2)]
    cursor.executemany("INSERT OR IGNORE INTO accommodations (type, total_quantity) VALUES (?, ?)", accommodations_to_add)
    holidays_to_add = [('Ano Novo 2026', '2025-12-30', '2026-01-02', 'Especial'), ('Carnaval 2026', '2026-02-13', '2026-02-18', 'Especial'),
                       ('7 de Setembro 2026', '2026-09-04', '2026-09-07', 'Especial'), ('Natal 2026', '2026-12-23', '2026-12-27', 'Especial')]
    cursor.executemany("INSERT OR IGNORE INTO holidays (name, start_date, end_date, type) VALUES (?, ?, ?, ?)", holidays_to_add)
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    if user_count == 0:
        print("BANCO DE DADOS DE USUÁRIOS VAZIO: Criando usuário 'admin' padrão...")
        from auth import hash_password
        username = "admin"
        password = "admin_password"
        hashed_password = hash_password(password)
        cursor.execute("INSERT INTO users (username, password_hash, first_name, last_name, email, role) VALUES (?, ?, ?, ?, ?, ?)",
                       (username, hashed_password, 'Admin', 'User', 'admin@40graus.com', 'admin'))
        print("Usuário 'admin' criado com sucesso.")

# --- Funções de CRUD para Usuários do Sistema ---
def add_system_user(username, password_hash, first_name, last_name, email, role):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash, first_name, last_name, email, role) VALUES (?, ?, ?, ?, ?, ?)", (username, password_hash, first_name, last_name, email, role))
            conn.commit()
        return True
    except sqlite3.IntegrityError: return False
def get_system_users():
    with sqlite3.connect(DB_FILE) as conn: return pd.read_sql_query("SELECT id, username, first_name, last_name, email, role FROM users", conn)
def update_system_user(user_id, first_name, last_name, email, role):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET first_name = ?, last_name = ?, email = ?, role = ? WHERE id = ?", (first_name, last_name, email, role, user_id))
            conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error: return False
def delete_system_user(user_id):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error: return False
def update_password(user_id, new_password_hash):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
            conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error: return False

# --- Funções de CRUD para Membros (Sócios) ---
def add_member(full_name, cpf, email, phone, birth_date, address, quota_type, usage_plan, start_date, end_date, payment_status):
    try:
        allowance_days = PLAN_ALLOWANCE_DAYS.get(usage_plan, 0)
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO members (full_name, cpf, email, phone, birth_date, address, quota_type, usage_plan, 
                                    allowance_days, used_days, start_date, end_date, payment_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (full_name, cpf, email, phone, birth_date, address, quota_type, usage_plan, 
                 allowance_days, 0, start_date, end_date, payment_status))
            conn.commit()
        return True
    except sqlite3.IntegrityError: return False

def get_all_members():
    with sqlite3.connect(DB_FILE) as conn: return pd.read_sql_query("SELECT id as ID, full_name as 'Nome Completo', cpf as CPF, email as Email, phone as Telefone, quota_type as Cota FROM members ORDER BY full_name", conn)
def get_member_by_id(member_id):
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        data = cursor.fetchone()
        return dict(data) if data else None
def update_member(member_id, full_name, cpf, email, phone, birth_date, address, quota_type, usage_plan, payment_status):
    try:
        allowance_days = PLAN_ALLOWANCE_DAYS.get(usage_plan, 0)
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""UPDATE members SET full_name=?, cpf=?, email=?, phone=?, birth_date=?, address=?,
                   quota_type=?, usage_plan=?, payment_status=?, allowance_days=? WHERE id=?""", 
                   (full_name, cpf, email, phone, birth_date, address, quota_type, usage_plan, payment_status, allowance_days, member_id))
            conn.commit()
        return cursor.rowcount > 0
    except sqlite3.IntegrityError: return False
def delete_member(member_id):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM members WHERE id = ?", (member_id,))
            conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error: return False
def get_member_allowance(member_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT allowance_days, used_days FROM members WHERE id = ?", (member_id,))
        result = cursor.fetchone()
        if result:
            return {"total": result[0], "used": result[1], "available": result[0] - result[1]}
        return None

# --- Funções de CRUD para Dependentes ---
def get_dependents(member_id):
    with sqlite3.connect(DB_FILE) as conn: return pd.read_sql_query("SELECT id, full_name as 'Nome Completo' FROM dependents WHERE member_id = ?", conn, params=(member_id,))
def add_dependent(member_id, full_name):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO dependents (member_id, full_name) VALUES (?, ?)", (member_id, full_name))
            conn.commit()
        return True
    except sqlite3.Error: return False
def delete_dependent(dependent_id):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dependents WHERE id = ?", (dependent_id,))
            conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error: return False

# --- Funções para o Dashboard ---
def get_dashboard_kpis():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM members")
        total_members = cursor.fetchone()[0]
        cursor.execute("SELECT value FROM settings WHERE key = 'simple_quota_price'")
        simple_price = float(cursor.fetchone()[0])
        cursor.execute("SELECT value FROM settings WHERE key = 'premium_quota_price'")
        premium_price = float(cursor.fetchone()[0])
        cursor.execute("SELECT COUNT(*) FROM members WHERE quota_type = 'Simples' AND payment_status = 'Pago'")
        paid_simple_members = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM members WHERE quota_type = 'Premium' AND payment_status = 'Pago'")
        paid_premium_members = cursor.fetchone()[0]
        total_revenue = (paid_simple_members * simple_price) + (paid_premium_members * premium_price)
        cursor.execute("SELECT SUM(total_quantity) FROM accommodations")
        total_units = cursor.fetchone()[0] or 0
        total_available_room_nights = total_units * 30
        start_period = date.today()
        end_period = start_period + timedelta(days=30)
        cursor.execute("SELECT SUM(julianday(end_date) - julianday(start_date)) FROM bookings WHERE status = 'Confirmada' AND start_date < ? AND end_date > ?", (end_period.isoformat(), start_period.isoformat()))
        booked_nights = cursor.fetchone()[0] or 0
        occupancy_rate = (booked_nights / total_available_room_nights) * 100 if total_available_room_nights > 0 else 0
        return {"total_members": total_members, "total_revenue": total_revenue, "occupancy_rate": occupancy_rate}
def get_members_by_quota_type():
    with sqlite3.connect(DB_FILE) as conn: return pd.read_sql_query("SELECT quota_type, COUNT(*) as count FROM members GROUP BY quota_type", conn)
def get_upcoming_checkins(days=7):
    with sqlite3.connect(DB_FILE) as conn:
        start_period = date.today()
        end_period = start_period + timedelta(days=days)
        query = """SELECT b.start_date as 'Check-in', m.full_name as 'Sócio', b.accommodation_type as 'Acomodação' FROM bookings b
                   JOIN members m ON b.member_id = m.id WHERE b.status = 'Confirmada' AND b.start_date BETWEEN ? AND ? ORDER BY b.start_date ASC"""
        return pd.read_sql_query(query, conn, params=(start_period.isoformat(), end_period.isoformat()))

# --- Funções de CRUD para Reservas (Bookings) ---
def check_availability(accommodation_type, start_date, end_date):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT total_quantity FROM accommodations WHERE type = ?", (accommodation_type,))
        result = cursor.fetchone()
        if not result: return 0
        total_quantity = result[0]
        cursor.execute("SELECT COUNT(*) FROM bookings WHERE accommodation_type = ? AND status = 'Confirmada' AND start_date < ? AND end_date > ?", (accommodation_type, end_date, start_date))
        booked_quantity = cursor.fetchone()[0]
        return total_quantity - booked_quantity
def add_booking(member_id, accommodation_type, start_date, end_date):
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        duration = (end - start).days
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("INSERT INTO bookings (member_id, accommodation_type, start_date, end_date, status) VALUES (?, ?, ?, ?, ?)", (member_id, accommodation_type, start_date, end_date, 'Confirmada'))
            cursor.execute("UPDATE members SET used_days = used_days + ? WHERE id = ?", (duration, member_id))
            conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Erro no banco de dados ao adicionar reserva: {e}")
        conn.rollback()
        return False
def get_all_bookings_for_calendar():
    with sqlite3.connect(DB_FILE) as conn:
        query = """SELECT b.id, b.start_date as start, b.end_date as end, m.full_name as member_name, b.accommodation_type as accommodation
                   FROM bookings b JOIN members m ON b.member_id = m.id WHERE b.status = 'Confirmada'"""
        df = pd.read_sql_query(query, conn)
    df['title'] = df['member_name'] + " (" + df['accommodation'] + ")"
    return df.to_dict('records')
def get_accommodation_types():
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT type FROM accommodations ORDER BY type", conn)
    return df['type'].tolist()
def get_all_bookings_with_details():
    """Busca todas as reservas com detalhes do sócio para exibição em tabela."""
    with sqlite3.connect(DB_FILE) as conn:
        query = """
            SELECT
                b.id as 'ID Reserva',
                m.full_name as 'Sócio',
                b.accommodation_type as 'Acomodação',
                b.start_date as 'Check-in',
                b.end_date as 'Check-out',
                b.status as 'Status'
            FROM bookings b
            JOIN members m ON b.member_id = m.id
            ORDER BY b.start_date DESC
        """
        return pd.read_sql_query(query, conn)
def update_booking_status(booking_id, new_status):
    """Atualiza o status de uma reserva e devolve as diárias se for cancelada."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            # Pega os detalhes da reserva antes de alterar
            cursor.execute("SELECT member_id, start_date, end_date, status FROM bookings WHERE id = ?", (booking_id,))
            booking_data = cursor.fetchone()
            if not booking_data: return False
            
            member_id, start_str, end_str, old_status = booking_data
            
            # Só faz algo se o status realmente mudar
            if old_status == new_status:
                return True

            cursor.execute("BEGIN TRANSACTION")
            # Atualiza o status da reserva
            cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", (new_status, booking_id))
            
            # Se a reserva estava confirmada e agora foi cancelada, devolve as diárias
            if old_status == 'Confirmada' and new_status == 'Cancelada':
                duration = (date.fromisoformat(end_str) - date.fromisoformat(start_str)).days
                cursor.execute("UPDATE members SET used_days = used_days - ? WHERE id = ?", (duration, member_id))
            
            conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Erro ao atualizar status da reserva: {e}")
        conn.rollback()
        return False
    
# --- Funções para a Página de Configurações ---
def get_all_settings():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        settings = {row[0]: row[1] for row in cursor.fetchall()}
        return settings
def update_setting(key, value):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
            conn.commit()
        return True
    except sqlite3.Error: return False
def get_all_accommodations():
    with sqlite3.connect(DB_FILE) as conn: return pd.read_sql_query("SELECT type as Tipo, total_quantity as Quantidade FROM accommodations", conn)
def update_accommodation_quantity(accommodation_type, quantity):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE accommodations SET total_quantity = ? WHERE type = ?", (quantity, accommodation_type))
            conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error: return False
def get_all_holidays():
    with sqlite3.connect(DB_FILE) as conn: return pd.read_sql_query("SELECT id, name as Nome, start_date as Início, end_date as Fim, type as Tipo FROM holidays ORDER BY start_date", conn)
def add_holiday(name, start_date, end_date, holiday_type):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO holidays (name, start_date, end_date, type) VALUES (?, ?, ?, ?)", (name, start_date, end_date, holiday_type))
            conn.commit()
        return True
    except sqlite3.Error: return False
def delete_holiday(holiday_id):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM holidays WHERE id = ?", (holiday_id,))
            conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error: return False

# --- Funções para Transações Financeiras ---
def add_transaction(member_id, amount, description, transaction_date):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO transactions (member_id, amount, description, transaction_date) VALUES (?, ?, ?, ?)", (member_id, amount, description, transaction_date))
            conn.commit()
        return True
    except sqlite3.Error: return False
def get_transactions_for_member(member_id):
    with sqlite3.connect(DB_FILE) as conn:
        query = "SELECT transaction_date as Data, description as Descrição, amount as Valor FROM transactions WHERE member_id = ? ORDER BY transaction_date DESC"
        df = pd.read_sql_query(query, conn, params=(member_id,))
    return df
def update_member_payment_status(member_id, new_status):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE members SET payment_status = ? WHERE id = ?", (new_status, member_id))
            conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error: return False