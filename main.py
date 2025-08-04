import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
# Jika Anda mengubah cakupan (scopes) ini, hapus file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_calendar():
    """
    Melakukan autentikasi dengan akun Google pengguna.
    Fungsi ini akan membuka browser untuk login saat pertama kali dijalankan.
    Setelah itu, kredensial akan disimpan di 'token.json' untuk penggunaan selanjutnya.
    """
    creds = None
    # File token.json menyimpan token akses dan refresh pengguna.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Jika tidak ada kredensial yang valid, minta pengguna untuk login.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Gagal me-refresh token, silakan otorisasi ulang. Hapus file 'token.json' dan jalankan lagi. Error: {e}")
                creds = None # Reset creds untuk memicu alur otorisasi baru
        
        if not creds:
            # Pastikan file 'credentials.json' yang Anda unduh dari Google Cloud ada di folder yang sama.
            if not os.path.exists('credentials.json'):
                print("Error: File 'credentials.json' tidak ditemukan.")
                print("Silakan unduh dari Google Cloud Console dan letakkan di folder yang sama dengan script ini.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Simpan kredensial untuk eksekusi berikutnya
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except HttpError as error:
        print(f'Terjadi error saat membangun service: {error}')
        return None

def create_event(service, calendar_id, event_data):
    """
    Membuat satu acara baru di kalender yang ditentukan.
    """
    event = {
        'summary': event_data['summary'],
        'description': event_data.get('description', ''), # Menambahkan deskripsi jika ada
        'start': {
            'date': event_data['start'],
            'timeZone': 'Asia/Jakarta', # Zona waktu Indonesia Barat
        },
        'end': {
            'date': event_data['end'],
            'timeZone': 'Asia/Jakarta',
        },
    }
    try:
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"Acara BERHASIL dibuat: '{event['summary']}' -> {created_event.get('htmlLink')}")
    except HttpError as error:
        print(f"GAGAL membuat acara '{event['summary']}'. Error: {error}")

def create_matkul_event(service, calendar_id, event_data):
    """
    Membuat acara untuk mata kuliah di kalender yang ditentukan.
    """
    event = {
        'summary': event_data['summary'],
        'description': event_data.get('description', ''), # Menambahkan deskripsi jika ada
        'start': {
            'dateTime': event_data['start'],
            'timeZone': 'Asia/Jakarta', # Zona waktu Indonesia Barat
        },
        'end': {
            'dateTime': event_data['end'],
            'timeZone': 'Asia/Jakarta',
        },
    }
    try:
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"Acara MATKUL BERHASIL dibuat: '{event['summary']}' -> {created_event.get('htmlLink')}")
    except HttpError as error:
        print(f"GAGAL membuat acara MATKUL '{event['summary']}'. Error: {error}")

def insert_event(service):
    """
    Fungsi untuk membaca data acara dari file JSON dan membuat acara di Google Calendar.
    """
    # Gunakan 'primary' untuk kalender utama Anda.
    calendar_id = 'primary'
    print(f"Akan menambahkan acara ke kalender: '{calendar_id}'")

    # Membaca data acara dari file JSON
    try:
        # Pastikan file 'events.json' berada di folder yang sama dengan skrip ini
        with open('events.json', 'r', encoding='utf-8') as f:
            events_data = json.load(f)
        
        # Validasi sederhana untuk memastikan file JSON tidak kosong dan berisi list
        if not isinstance(events_data, list) or not events_data:
            print("Error: File 'events.json' tidak berisi daftar acara yang valid atau kosong.")
            return

    except FileNotFoundError:
        print("Error: File 'events.json' tidak ditemukan. Pastikan file tersebut ada di folder yang sama.")
        return
    except json.JSONDecodeError:
        print("Error: Gagal mem-parsing file 'events.json'. Pastikan formatnya benar.")
        return

    for event_info in events_data:
        create_event(service, calendar_id, event_info)

    print("\nSemua acara telah selesai diproses.")

def insert_matkul_event(service):
    """
    Fungsi untuk membaca data acara mata kuliah dari file JSON dan membuat acara di Google Calendar.
    """
    # Gunakan 'primary' untuk kalender utama Anda.
    calendar_id = 'primary'
    print(f"Akan menambahkan acara MATKUL ke kalender: '{calendar_id}'")

    # Membaca data acara mata kuliah dari file JSON
    try:
        # Pastikan file 'matkul_events.json' berada di folder yang sama dengan skrip ini
        with open('matkul_events.json', 'r', encoding='utf-8') as f:
            matkul_events_data = json.load(f)
        
        # Validasi sederhana untuk memastikan file JSON tidak kosong dan berisi list
        if not isinstance(matkul_events_data, list) or not matkul_events_data:
            print("Error: File 'matkul_events.json' tidak berisi daftar acara yang valid atau kosong.")
            return

    except FileNotFoundError:
        print("Error: File 'matkul_events.json' tidak ditemukan. Pastikan file tersebut ada di folder yang sama.")
        return
    except json.JSONDecodeError:
        print("Error: Gagal mem-parsing file 'matkul_events.json'. Pastikan formatnya benar.")
        return

    for event_info in matkul_events_data:
        create_matkul_event(service, calendar_id, event_info)

    print("\nSemua acara MATKUL telah selesai diproses.")

def main():
    """
    Fungsi utama untuk menjalankan seluruh proses:
    1. Autentikasi
    2. Membaca data acara dari file JSON
    3. Membuat setiap acara di Google Calendar
    """
    service = authenticate_google_calendar()
    
    if not service:
        print("Proses dihentikan karena autentikasi gagal.")
        return

    while True:
        print("\n--- MENU UTAMA (CALENDAR & TASKS) ---")
        print("1. Tambahkan Kalender Akademik ke Google CALENDAR")
        print("2. Tambahkan Tugas Baru ke Google TASKS")
        print("3. Keluar")
        
        choice = input("Masukkan pilihan Anda (1/2/3): ")
        
        if choice == '1':
            insert_event(service)
        elif choice == '2':
            insert_matkul_event(service)
        elif choice == '3':
            print("Keluar dari program. Sampai jumpa!")
            break
        else:
            print("Pilihan tidak valid, silakan coba lagi.")

if __name__ == '__main__':
    main()