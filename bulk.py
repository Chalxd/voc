import asyncio
import os
from telethon import TelegramClient
from colorama import init, Fore, Style

# Inisialisasi Colorama
init(autoreset=True)

# ==========================================
# 1. KONFIGURASI TELEGRAM API & SETTING
# ==========================================
API_ID = 1234567               # Masukkan API_ID akun Telegram kamu (dalam angka)
API_HASH = 'isi_api_hash_disini' # Masukkan API_HASH akun Telegram kamu

BOT_USERNAME = '@shp_tools_bot'   # Username bot target
ACCOUNTS_FILE = 'account.txt'     # Sumber list akun
DOWNLOAD_DIR = 'downloads'        # Folder temporary download HTML

# Nama file output terpisah
VOUCER_TARGET_FILE = 'voucer.txt'
MISSION_TARGET_FILE = 'mission.txt'

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
client = TelegramClient('session_checker', API_ID, API_HASH)

def remove_duplicates_from_file(file_path):
    """Fungsi untuk membersihkan akun duplikat di file target agar bersih dari human error"""
    if not os.path.exists(file_path):
        return
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        unique_lines = []
        seen = set()
        for line in lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
                
        with open(file_path, 'w', encoding='utf-8') as f:
            for line in unique_lines:
                f.write(f"{line}\n")
    except Exception as e:
        print(Fore.RED + f"    [!] Error saat membersihkan duplikat file: {e}")

def validate_voucher_html(file_path):
    """Fungsi buat ngecek apakah file HTML punya 2 voucher wajib (12RB & 25RB)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        req1 = ("SPPSH243300087635331" in content) or ("Diskon Ongkir Rp12RB - Tanpa min. belanja" in content)
        req2 = ("SPPSF203300087635331" in content) or ("Diskon 100% s.d. Rp25RB - Tanpa min. belanja" in content)
        
        return req1 and req2
    except Exception as e:
        print(Fore.RED + f"    [!] Error baca file HTML: {e}")
        return False

async def process_voucher_account(account_input):
    print(Fore.CYAN + f"\n========================================")
    print(Fore.CYAN + f"[+] Memproses Akun (Voucher): {account_input}")
    print(Fore.CYAN + f"========================================")

    # Step 1: Kirim /account
    print(Fore.YELLOW + "[1] Mengirim perintah /account...")
    await client.send_message(BOT_USERNAME, '/account')
    await asyncio.sleep(3)

    # Step 2: Cari & Klik Tombol "Check Voucher"
    print(Fore.YELLOW + "[2] Mencari tombol 'Check Voucher'...")
    messages = await client.get_messages(BOT_USERNAME, limit=1)
    
    clicked_cv = False
    if messages and messages[0].buttons:
        for row in messages[0].buttons:
            for button in row:
                if 'check voucher' in button.text.lower():
                    await button.click()
                    clicked_cv = True
                    print(Fore.GREEN + f"    -> Berhasil klik tombol: '{button.text}'")
                    break
            if clicked_cv:
                break

    if not clicked_cv:
        print(Fore.RED + "    [!] GAGAL: Tombol 'Check Voucher' tidak ditemukan!")
        return False

    await asyncio.sleep(3)

    # Step 3: Cari & Klik Tombol "Email / Username / ID"
    print(Fore.YELLOW + "[3] Mencari tombol 'Email / Username / ID'...")
    messages = await client.get_messages(BOT_USERNAME, limit=1)
    
    clicked_email_btn = False
    if messages and messages[0].buttons:
        for row in messages[0].buttons:
            for button in row:
                if 'email' in button.text.lower() or 'username' in button.text.lower() or 'id' in button.text.lower():
                    await button.click()
                    clicked_email_btn = True
                    print(Fore.GREEN + f"    -> Berhasil klik tombol: '{button.text}'")
                    break
            if clicked_email_btn:
                break

    if not clicked_email_btn:
        print(Fore.RED + "    [!] GAGAL: Tombol 'Email / Username / ID' tidak ditemukan!")
        return False

    await asyncio.sleep(3)

    # Step 4: Kirim data akun
    print(Fore.YELLOW + f"[4] Mengirim data akun: {account_input}...")
    await client.send_message(BOT_USERNAME, account_input)
    
    print(Fore.YELLOW + "[*] Menunggu bot mengirim file HTML...")
    
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
        print(Fore.RED + "    [!] TIMEOUT: Bot tidak mengirimkan file HTML.")
        return False

    print(Fore.GREEN + f"    [✓] File HTML berhasil diunduh.")

    # Step 6: Validasi Isi HTML
    print(Fore.YELLOW + "[6] Memfilter voucher di dalam HTML...")
    if validate_voucher_html(html_path):
        existing_accounts = set()
        if os.path.exists(VOUCER_TARGET_FILE):
            with open(VOUCER_TARGET_FILE, 'r', encoding='utf-8') as tf:
                existing_accounts = {line.strip() for line in tf if line.strip()}
        
        if account_input not in existing_accounts:
            with open(VOUCER_TARGET_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{account_input}\n")
            print(Fore.GREEN + f"    [VALID] Akun {account_input} memiliki voucher lengkap! Disimpan ke '{VOUCER_TARGET_FILE}'.")
        else:
            print(Fore.MAGENTA + f"    [-] Akun {account_input} sudah ada di '{VOUCER_TARGET_FILE}' (Duplicate terdeteksi, diabaikan).")
        return True
    else:
        print(Fore.RED + f"    [-] Akun {account_input} tidak memenuhi syarat voucher (tidak lengkap).")
        return False

async def process_mission_account(account_input):
    # Step 1: Kirim /mission[cite: 3]
    await client.send_message(BOT_USERNAME, '/mission')
    await asyncio.sleep(3)

    # Step 2: Cari & Klik Tombol "Misi Checkin"[cite: 3]
    messages = await client.get_messages(BOT_USERNAME, limit=1)
    clicked_misi = False
    if messages and messages[0].buttons:
        for row in messages[0].buttons:
            for button in row:
                if 'misi checkin' in button.text.lower():
                    await button.click()
                    clicked_misi = True
                    break
            if clicked_misi:
                break

    if not clicked_misi:
        return False

    await asyncio.sleep(4)

    # Step 3: Cari & Klik Tombol "Email / Username / ID"[cite: 3]
    messages = await client.get_messages(BOT_USERNAME, limit=1)
    clicked_email_btn = False
    if messages and messages[0].buttons:
        for row in messages[0].buttons:
            for button in row:
                if 'email' in button.text.lower() or 'username' in button.text.lower():
                    await button.click()
                    clicked_email_btn = True
                    break
            if clicked_email_btn:
                break

    if not clicked_email_btn:
        return False

    await asyncio.sleep(3)

    # Step 4: Kirim data akun[cite: 3]
    await client.send_message(BOT_USERNAME, account_input)
    await asyncio.sleep(5)

    # Step 5: Cek balasan pesan dari bot dan cetak ala terminal aesthetic[cite: 3, 4]
    response_messages = await client.get_messages(BOT_USERNAME, limit=3)
    target_msg = None
    for msg in response_messages:
        text = msg.text or ""
        if "Misi Checkin" in text or "Install ShopeePay" in text or "Isi Saldo" in text:
            target_msg = text
            break
            
    if target_msg:
        lines = target_msg.splitlines()
        
        # Cetak rincian pesan misi persis seperti gaya di gambar
        print("")
        for line in lines:
            print(Fore.WHITE + line)
            
        uncompleted_missions = [line.strip() for line in lines if "belum selesai" in line.strip().lower()]

        if uncompleted_missions:
            existing_accounts = set()
            if os.path.exists(MISSION_TARGET_FILE):
                with open(MISSION_TARGET_FILE, 'r', encoding='utf-8') as tf:
                    existing_accounts = {line.strip() for line in tf if line.strip()}
            
            if account_input not in existing_accounts:
                with open(MISSION_TARGET_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"{account_input}\n")
                print(Fore.GREEN + f"========================================")
                print(Fore.GREEN + f"🔥 SUCCESS | Akun: {account_input}")
                print(Fore.GREEN + f"========================================")
            else:
                print(Fore.MAGENTA + f"========================================")
                print(Fore.MAGENTA + f"⚠️ DUPLICATE | Akun {account_input} sudah ada di file.")
                print(Fore.MAGENTA + f"========================================")
            return True
            
    print(Fore.RED + f"[-] Akun {account_input} tidak memiliki misi yang belum selesai.")
    return False

async def main():
    await client.start()
    print(Fore.GREEN + "[*] Telegram Client Berjalan...")

    print(Fore.BLUE + "\n" + "="*40)
    print(Fore.YELLOW + "         PILIH MENU UTAMA BOT CHECKER")
    print(Fore.BLUE + "="*40)
    print(Fore.WHITE + "1. Check Voucher 25K + 12K (Output: voucer.txt)")
    print(Fore.WHITE + "2. Check Mission          (Output: mission.txt)")
    print(Fore.BLUE + "="*40)
    
    choice = input(Fore.CYAN + "Masukkan pilihan (1 atau 2): " + Style.RESET_ALL).strip()

    if choice not in ['1', '2']:
        print(Fore.RED + "[ERROR] Pilihan tidak valid!")
        return

    active_target_file = VOUCER_TARGET_FILE if choice == '1' else MISSION_TARGET_FILE

    if not os.path.exists(ACCOUNTS_FILE):
        print(Fore.RED + f"[ERROR] File '{ACCOUNTS_FILE}' tidak ditemukan!")
        return

    with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
        accounts = []
        seen_input = set()
        for line in f:
            acc = line.strip()
            if acc and acc not in seen_input:
                seen_input.add(acc)
                accounts.append(acc)

    if not accounts:
        print(Fore.RED + f"[!] File '{ACCOUNTS_FILE}' kosong.")
        return

    remove_duplicates_from_file(active_target_file)

    total_accounts = len(accounts)
    print(Fore.YELLOW + f"[i] Total akun unik yang akan diperiksa: {total_accounts}")

    valid_count = 0
    invalid_count = 0

    for index, account in enumerate(accounts, start=1):
        print(Fore.CYAN + f"\nProgress: [{index}/{total_accounts}] Memproses akun: {account}")
        
        if choice == '1':
            is_valid = await process_voucher_account(account)
        else:
            is_valid = await process_mission_account(account)
        
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
        
        if index < total_accounts:
            print(Fore.YELLOW + "[*] Jeda 3 detik...")
            await asyncio.sleep(3)

    remove_duplicates_from_file(active_target_file)

    print(Fore.BLUE + "\n" + "="*40)
    print(Fore.GREEN + "            REKAPITULASI HASIL CHECKER")
    print(Fore.BLUE + "="*40)
    print(Fore.WHITE + f"Total Akun Dicek     : {total_accounts}")
    print(Fore.GREEN + f"Akun Lolos (Valid)   : {valid_count}")
    print(Fore.RED + f"Akun Tidak Lolos     : {invalid_count}")
    print(Fore.BLUE + "="*40)
    print(Fore.GREEN + f"[✓] Selesai! Akun valid (bebas duplikat) tersimpan di file '{active_target_file}'.")

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())