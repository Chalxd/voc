# Telegram Voucher Checker

Bot script untuk otomatisasi pemeriksaan voucher via bot Telegram (`@shp_tools_bot`).

## Panduan Jalankan di Termux

1. **Update & Install Python + Unzip:**
   ```bash
   pkg update && pkg upgrade -y
   pkg install python unzip -y
   ```

2. **Ekstrak File ZIP:**
   ```bash
   unzip telegram_voucher_checker_v2.zip
   cd telegram_voucher_checker
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Pengaturan Konfigurasi & Akun:**
   - Buka file `bot.py` dan masukkan `API_ID` serta `API_HASH` Telegram kamu di bagian atas.
   - Buka file `account.txt` dan masukkan daftar email/username/ID yang mau dicek (1 akun per baris).

5. **Jalankan Bot:**
   ```bash
   python bot.py
   ```
