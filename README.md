# pythondep
cara menjalankan aplikasi ini sangat sederhana. pertama simpan seluruh kode ke dalam satu file bernama nabung_uang.py. setelah itu buka terminal atau command prompt, lalu arahkan ke folder tempat file tersebut disimpan. untuk memulai program, jalankan perintah berikut:
python nabung_uang.py
# fitur aplikasi
autentikasi pengguna:
register dan login untuk user
login admin (username: admin, password: admin123)
# fitur user:
setor uang (deposit) dengan status pending
tarik uang (withdraw) dengan status pending
cek saldo
lihat riwayat transaksi
# fitur admin:
verifikasi transaksi pending (setujui atau tolak)
lihat semua riwayat transaksi
# keamanan:
password di-hash menggunakan sha-256
validasi input pengguna
# database:
sqlite dengan dua tabel (users dan transactions)
sudah ada data seed untuk admin default
# catatan penting
aplikasi ini self-contained, tidak membutuhkan framework web
setiap transaksi harus diverifikasi admin sebelum mempengaruhi saldo
saldo user hanya akan berubah jika transaksi disetujui admin
admin bisa melihat semua transaksi, sedangkan user hanya bisa melihat transaksinya sendiri
