import sqlite3
import hashlib
import getpass
from datetime import datetime

class NabungUangApp:
    def __init__(self, db_name='nabung_uang.db'):
        self.db_name = db_name
        self.current_user = None
        self.is_admin = False
        self.init_db()
        self.seed_data()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Tabel users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                balance REAL DEFAULT 0
            )
        ''')
        
        # Tabel transactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified_by INTEGER,
                verified_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (verified_by) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def seed_data(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Cek jika admin sudah ada
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            # Buat admin default
            admin_password_hash = self.hash_password('admin123')
            cursor.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                ('admin', admin_password_hash, 1)
            )
            print("Admin default created: username='admin', password='admin123'")
        
        conn.commit()
        conn.close()

    def register(self):
        print("\n--- REGISTRASI USER BARU ---")
        username = input("Username: ").strip()
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Cek jika username sudah ada
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            print("Username sudah terdaftar!")
            conn.close()
            return False
        
        password = getpass.getpass("Password: ")
        password_hash = self.hash_password(password)
        
        # Buat user baru
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        
        conn.commit()
        conn.close()
        print("Registrasi berhasil! Silakan login.")
        return True

    def login(self):
        print("\n--- LOGIN ---")
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        password_hash = self.hash_password(password)
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, username, is_admin, balance FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            self.current_user = {
                'id': user[0],
                'username': user[1],
                'is_admin': bool(user[2]),
                'balance': user[3]
            }
            self.is_admin = bool(user[2])
            print(f"Login berhasil! Selamat datang {user[1]}")
            return True
        else:
            print("Username atau password salah!")
            return False

    def logout(self):
        self.current_user = None
        self.is_admin = False
        print("Logout berhasil!")

    def deposit(self):
        if not self.current_user:
            print("Silakan login terlebih dahulu!")
            return
        
        print("\n--- SETOR UANG ---")
        try:
            amount = float(input("Jumlah uang yang akan disetor: "))
            if amount <= 0:
                print("Jumlah harus lebih dari 0!")
                return
        except ValueError:
            print("Masukkan jumlah yang valid!")
            return
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Buat transaksi deposit
        cursor.execute(
            "INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)",
            (self.current_user['id'], 'deposit', amount)
        )
        
        conn.commit()
        conn.close()
        print("Permintaan setor uang berhasil diajukan. Menunggu verifikasi admin.")

    def withdraw(self):
        if not self.current_user:
            print("Silakan login terlebih dahulu!")
            return
        
        print("\n--- TARIK UANG ---")
        try:
            amount = float(input("Jumlah uang yang akan ditarik: "))
            if amount <= 0:
                print("Jumlah harus lebih dari 0!")
                return
        except ValueError:
            print("Masukkan jumlah yang valid!")
            return
        
        # Cek saldo cukup
        if self.current_user['balance'] < amount:
            print("Saldo tidak cukup!")
            return
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Buat transaksi withdraw
        cursor.execute(
            "INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)",
            (self.current_user['id'], 'withdraw', amount)
        )
        
        conn.commit()
        conn.close()
        print("Permintaan tarik uang berhasil diajukan. Menunggu verifikasi admin.")

    def check_balance(self):
        if not self.current_user:
            print("Silakan login terlebih dahulu!")
            return
        
        print(f"\nSaldo Anda saat ini: Rp {self.current_user['balance']:,.2f}")

    def transaction_history(self):
        if not self.current_user:
            print("Silakan login terlebih dahulu!")
            return
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        if self.is_admin:
            # Admin bisa melihat semua transaksi
            cursor.execute('''
                SELECT t.id, u.username, t.type, t.amount, t.status, t.created_at, 
                       v.username, t.verified_at
                FROM transactions t
                JOIN users u ON t.user_id = u.id
                LEFT JOIN users v ON t.verified_by = v.id
                ORDER BY t.created_at DESC
            ''')
        else:
            # User hanya bisa melihat transaksinya sendiri
            cursor.execute('''
                SELECT t.id, u.username, t.type, t.amount, t.status, t.created_at, 
                       v.username, t.verified_at
                FROM transactions t
                JOIN users u ON t.user_id = u.id
                LEFT JOIN users v ON t.verified_by = v.id
                WHERE t.user_id = ?
                ORDER BY t.created_at DESC
            ''', (self.current_user['id'],))
        
        transactions = cursor.fetchall()
        conn.close()
        
        print("\n--- RIWAYAT TRANSAKSI ---")
        if not transactions:
            print("Tidak ada transaksi.")
            return
        
        for t in transactions:
            status = t[4]
            status_display = "DITERIMA" if status == 'approved' else "DITOLAK" if status == 'rejected' else "MENUNGGU"
            verified_by = f" oleh {t[6]}" if t[6] else ""
            verified_at = f" pada {t[7]}" if t[7] else ""
            
            print(f"{t[5]} - {t[2].upper()} {t[1]}: Rp {t[3]:,.2f} - {status_display}{verified_by}{verified_at}")

    def admin_pending_transactions(self):
        if not self.is_admin:
            print("Hanya admin yang dapat mengakses fitur ini!")
            return
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Ambil transaksi yang pending
        cursor.execute('''
            SELECT t.id, u.username, t.type, t.amount, t.created_at
            FROM transactions t
            JOIN users u ON t.user_id = u.id
            WHERE t.status = 'pending'
            ORDER BY t.created_at
        ''')
        
        pending_transactions = cursor.fetchall()
        
        if not pending_transactions:
            print("Tidak ada transaksi yang menunggu verifikasi.")
            conn.close()
            return
        
        print("\n--- TRANSAKSI MENUNGGU VERIFIKASI ---")
        for i, t in enumerate(pending_transactions, 1):
            print(f"{i}. {t[4]} - {t[2].upper()} {t[1]}: Rp {t[3]:,.2f}")
        
        try:
            choice = int(input("\nPilih nomor transaksi untuk diverifikasi (0 untuk batal): "))
            if choice == 0:
                conn.close()
                return
            if choice < 1 or choice > len(pending_transactions):
                print("Pilihan tidak valid!")
                conn.close()
                return
        except ValueError:
            print("Masukkan angka yang valid!")
            conn.close()
            return
        
        selected_transaction = pending_transactions[choice-1]
        transaction_id = selected_transaction[0]
        user_id = cursor.execute("SELECT user_id FROM transactions WHERE id = ?", (transaction_id,)).fetchone()[0]
        transaction_type = selected_transaction[2]
        amount = selected_transaction[3]
        
        print("\nPilihan:")
        print("1. Setujui transaksi")
        print("2. Tolak transaksi")
        print("3. Batal")
        
        try:
            action = int(input("Pilih action: "))
            if action == 1:  # Setujui
                # Update saldo user
                if transaction_type == 'deposit':
                    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
                else:  # withdraw
                    cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, user_id))
                
                # Update status transaksi
                cursor.execute(
                    "UPDATE transactions SET status = 'approved', verified_by = ?, verified_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (self.current_user['id'], transaction_id)
                )
                print("Transaksi disetujui.")
                
            elif action == 2:  # Tolak
                # Update status transaksi
                cursor.execute(
                    "UPDATE transactions SET status = 'rejected', verified_by = ?, verified_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (self.current_user['id'], transaction_id)
                )
                print("Transaksi ditolak.")
            else:
                print("Dibatalkan.")
                conn.commit()
                conn.close()
                return
                
            conn.commit()
            
        except ValueError:
            print("Masukkan angka yang valid!")
        
        conn.close()

    def run(self):
        print("=== APLIKASI NABUNG UANG ===")
        
        while True:
            if not self.current_user:
                print("\nMenu:")
                print("1. Login")
                print("2. Register")
                print("3. Keluar")
                
                try:
                    choice = int(input("Pilih menu: "))
                    if choice == 1:
                        self.login()
                    elif choice == 2:
                        self.register()
                    elif choice == 3:
                        print("Terima kasih! Sampai jumpa.")
                        break
                    else:
                        print("Pilihan tidak valid!")
                except ValueError:
                    print("Masukkan angka yang valid!")
            else:
                if self.is_admin:
                    print("\nMenu Admin:")
                    print("1. Lihat Riwayat Transaksi")
                    print("2. Verifikasi Transaksi Pending")
                    print("3. Logout")
                else:
                    print("\nMenu User:")
                    print("1. Setor Uang")
                    print("2. Tarik Uang")
                    print("3. Cek Saldo")
                    print("4. Lihat Riwayat Transaksi")
                    print("5. Logout")
                
                try:
                    choice = int(input("Pilih menu: "))
                    if self.is_admin:
                        if choice == 1:
                            self.transaction_history()
                        elif choice == 2:
                            self.admin_pending_transactions()
                        elif choice == 3:
                            self.logout()
                        else:
                            print("Pilihan tidak valid!")
                    else:
                        if choice == 1:
                            self.deposit()
                        elif choice == 2:
                            self.withdraw()
                        elif choice == 3:
                            self.check_balance()
                        elif choice == 4:
                            self.transaction_history()
                        elif choice == 5:
                            self.logout()
                        else:
                            print("Pilihan tidak valid!")
                except ValueError:
                    print("Masukkan angka yang valid!")

if __name__ == "__main__":
    app = NabungUangApp()
    app.run()