import asyncio
import os
from telethon import TelegramClient

# ==========================================
# 1. KONFIGURASI TELEGRAM API
# ==========================================
API_ID =       apilu        # Ganti dengan API ID kamu
API_HASH = 'apilu' # Ganti dengan API HASH kamu

BOT_USERNAME = '@shp_tools_bot'  # Sesuaikan dengan username bot
ACCOUNTS_FILE = 'account.txt'
OUTPUT_FILE = 'hasil_akun.txt'

client = TelegramClient('session_checker', API_ID, API_HASH)

async def process_account(account_input):
    print(f"\n========================================")
    print(f"[+] Memproses akun: {account_input}")
    print(f"========================================")

    # Step 1: Kirim /mission
    print("[1] Mengirim /mission...")
    await client.send_message(BOT_USERNAME, '/mission')
    await asyncio.sleep(3)

    # Step 2: Cari & Klik Tombol "Misi Checkin"
    print("[2] Mencari tombol 'Misi Checkin'...")
    messages = await client.get_messages(BOT_USERNAME, limit=1)
    
    clicked_misi = False
    if messages and messages[0].buttons:
        for row in messages[0].buttons:
            for button in row:
                if 'misi checkin' in button.text.lower():
                    await button.click()
                    clicked_misi = True
                    print(f"    -> Berhasil klik tombol: '{button.text}'")
                    break
            if clicked_misi:
                break

    if not clicked_misi:
        print("    [!] GAGAL: Tombol 'Misi Checkin' tidak ditemukan!")
        return False, []

    await asyncio.sleep(4)

    # Step 3: Cari & Klik Tombol "Email / Username / ID"
    print("[3] Mencari tombol 'Email / Username / ID'...")
    messages = await client.get_messages(BOT_USERNAME, limit=1)
    
    clicked_email_btn = False
    if messages and messages[0].buttons:
        for row in messages[0].buttons:
            for button in row:
                if 'email' in button.text.lower() or 'username' in button.text.lower():
                    await button.click()
                    clicked_email_btn = True
                    print(f"    -> Berhasil klik tombol: '{button.text}'")
                    break
            if clicked_email_btn:
                break

    if not clicked_email_btn:
        print("    [!] GAGAL: Tombol 'Email / Username / ID' tidak ditemukan!")
        return False, []

    await asyncio.sleep(3)

    # Step 4: Kirim Email / Username / ID dari accounts.txt
    print(f"[4] Mengirim data akun: {account_input}...")
    await client.send_message(BOT_USERNAME, account_input)
    
    print("[*] Menunggu respons rincian misi dari bot...")
    await asyncio.sleep(5)

    # Step 5: Ambil balasan pesan terbaru dari bot
    response_messages = await client.get_messages(BOT_USERNAME, limit=3)
    
    target_msg = None
    for msg in response_messages:
        text = msg.text or ""
        if "Misi Checkin" in text or "Install ShopeePay" in text or "Isi Saldo" in text:
            target_msg = text
            break
            
    if target_msg:
        lines = target_msg.splitlines()
        uncompleted_missions = []
        
        for line in lines:
            line_str = line.strip()
            # Hanya ambil baris misi yang mengandung kata kunci "belum selesai"
            if "belum selesai" in line_str.lower():
                uncompleted_missions.append(line_str)

        # Jika ada misi yang "belum selesai", simpan ke hasil_akun.txt
        if uncompleted_missions:
            with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                f.write(f"=== HASIL UNTUK: {account_input} ===\n")
                for mission in uncompleted_missions:
                    f.write(f"{mission}\n")
                f.write("\n" + "="*40 + "\n\n")
            print(f"[✓] Akun memiliki misi 'belum selesai'. Disimpan ke: {OUTPUT_FILE}")
            return True, uncompleted_missions
        else:
            print("[i] Akun tidak memiliki misi 'belum selesai' (semua sudah selesai/tidak ada).")
            return False, []
    else:
        print("[!] Tidak ada balasan misi dari bot.")
        return False, []

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

    has_mission_count = 0
    no_mission_count = 0

    for index, account in enumerate(accounts, start=1):
        print(f"\nProgress: [{index}/{total_accounts}]")
        has_mission, _ = await process_account(account)
        
        if has_mission:
            has_mission_count += 1
        else:
            no_mission_count += 1
        
        if index < total_accounts:
            print("[*] Jeda 4 detik...")
            await asyncio.sleep(4)

    # Menampilkan Rekapitulasi Akhir
    print("\n" + "="*40)
    print("           REKAPITULASI HASIL CHECK")
    print("="*40)
    print(f"Total Akun Dicek     : {total_accounts}")
    print(f"Akun Ada Misi        : {has_mission_count}")
    print(f"Akun Tidak Ada Misi  : {no_mission_count}")
    print("="*40)
    print(f"[✓] Selesai! Hasil tersimpan di file '{OUTPUT_FILE}'.")

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())