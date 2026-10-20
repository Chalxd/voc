import asyncio
import os
from telethon import TelegramClient
from bs4 import BeautifulSoup

# ==========================================
# 1. KONFIGURASI TELEGRAM API & SETTING
# ==========================================
API_ID = 1234567               # Masukkan API_ID akun Telegram kamu (dalam angka)
API_HASH = 'isi_api_hash_disini' # Masukkan API_HASH akun Telegram kamu

BOT_USERNAME = '@shp_tools_bot'   # Username bot target
ACCOUNTS_FILE = 'account.txt'     # Sumber list akun
TARGET_FILE = 'target.txt'        # Output akun yang lolos filter
DOWNLOAD_DIR = 'downloads'        # Folder temporary download HTML

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
client = TelegramClient('session_checker', API_ID, API_HASH)

def validate_voucher_html(file_path):
    """Fungsi buat ngecek apakah file HTML punya 2 voucher wajib (12RB & 25RB)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Syarat 1: Voucher Ongkir 12RB
        req1 = ("SPPSH243300087635331" in content) or ("Diskon Ongkir Rp12RB - Tanpa min. belanja" in content)
        
        # Syarat 2: Voucher Diskon 100% 25RB
        req2 = ("SPPSF203300087635331" in content) or ("Diskon 100% s.d. Rp25RB - Tanpa min. belanja" in content)
        
        return req1 and req2
    except Exception as e:
        print(f"    [!] Error baca file HTML: {e}")
        return False

async def process_account(account_input):
    print(f"\n========================================")
    print(f"[+] Memproses akun: {account_input}")
    print(f"========================================")

    # Step 1: Kirim /account
    print("[1] Mengirim perintah /account...")
    await client.send_message(BOT_USERNAME, '/account')
    await asyncio.sleep(3)

    # Step 2: Cari & Klik Tombol "Check Voucher"
    print("[2] Mencari tombol 'Check Voucher'...")
    messages = await client.get_messages(BOT_USERNAME, limit=1)
    
    clicked_cv = False
    if messages and messages[0].buttons:
        for row in messages[0].buttons:
            for button in row:
                if 'check voucher' in button.text.lower():
                    await button.click()
                    clicked_cv = True
                    print(f"    -> Berhasil klik tombol: '{button.text}'")
                    break
            if clicked_cv:
                break

    if not clicked_cv:
        print("    [!] GAGAL: Tombol 'Check Voucher' tidak ditemukan!")
        return False

    await asyncio.sleep(3)

    # Step 3: Cari & Klik Tombol "Email / Username / ID"
    print("[3] Mencari tombol 'Email / Username / ID'...")
    messages = await client.get_messages(BOT_USERNAME, limit=1)
    
    clicked_email_btn = False
    if messages and messages[0].buttons:
        for row in messages[0].buttons:
            for button in row:
                if 'email' in button.text.lower() or 'username' in button.text.lower() or 'id' in button.text.lower():
                    await button.click()
                    clicked_email_btn = True
                    print(f"    -> Berhasil klik tombol: '{button.text}'")
                    break
            if clicked_email_btn:
                break

    if not clicked_email_btn:
        print("    [!] GAGAL: Tombol 'Email / Username / ID' tidak ditemukan!")
        return False

    await asyncio.sleep(3)

    # Step 4: Kirim Email / Username / ID dari account.txt
    print(f"[4] Mengirim data akun: {account_input}...")
    await client.send_message(BOT_USERNAME, account_input)
    
    print("[*] Menunggu bot mengirim file HTML...")
    
    # Step 5: Tunggu balasan berupa file HTML dari bot (maksimal 15 detik)
    file_received = False
    html_path = ""
    
    for _ in range(15):
        await asyncio.sleep(3)
        response_messages = await client.get_messages(BOT_USERNAME, limit=3)
        for msg in response_messages:
            if msg.document:
                for attr in msg.document.attributes:
                    if hasattr(attr, 'file_name') and attr.file_name and attr.file_name.endswith('.html'):
                        html_path = os.path.join(DOWNLOAD_DIR, f"{account_input}.html")
                        await msg.download_media(html_path)
                        file_received = True
                        break
            if file_received:
                break
        if file_received:
            break

    if not file_received:
        print("    [!] TIMEOUT: Bot tidak mengirimkan file HTML.")
        return False

    print(f"    [✓] File HTML berhasil diunduh.")

    # Step 6: Validasi Isi HTML (Filter Voucher 12RB & 25RB)
    print("[6] Memfilter voucher di dalam HTML...")
    if validate_voucher_html(html_path):
        with open(TARGET_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{account_input}\n")
        print(f"    [VALID] Akun {account_input} memiliki voucher lengkap! Disimpan ke '{TARGET_FILE}'.")
        return True
    else:
        print(f"    [-] Akun {account_input} tidak memenuhi syarat voucher (tidak lengkap).")
        return False

async def main():
    await client.start()
    print("[*] Telegram Client Berjalan...")

    if not os.path.exists(ACCOUNTS_FILE):
        print(f"[ERROR] File '{ACCOUNTS_FILE}' tidak ditemukan!")
        return

    with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
        accounts = [line.strip() for line in f if line.strip()]

    if not accounts:
        print(f"[!] File '{ACCOUNTS_FILE}' kosong.")
        return

    total_accounts = len(accounts)
    print(f"[i] Total akun yang akan diperiksa: {total_accounts}")

    valid_count = 0
    invalid_count = 0

    for index, account in enumerate(accounts, start=1):
        print(f"\nProgress: [{index}/{total_accounts}]")
        is_valid = await process_account(account)
        
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
        
        if index < total_accounts:
            print("[*] Jeda 3 detik...")
            await asyncio.sleep(3)

    # Rekapitulasi Akhir
    print("\n" + "="*40)
    print("            REKAPITULASI HASIL CHECK VOUCHER")
    print("="*40)
    print(f"Total Akun Dicek     : {total_accounts}")
    print(f"Akun Lolos (Valid)   : {valid_count}")
    print(f"Akun Tidak Lolos     : {invalid_count}")
    print("="*40)
    print(f"[✓] Selesai! Akun valid tersimpan di file '{TARGET_FILE}'.")

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())
