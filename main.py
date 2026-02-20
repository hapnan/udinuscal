import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow # type: ignore
from googleapiclient.discovery import build # type: ignore
from googleapiclient.errors import HttpError

# Jika Anda mengubah cakupan (scopes) ini, hapus file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
TIMEZONE = 'Asia/Jakarta'
CALENDAR_ID = 'primary'
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'


def authenticate_google_calendar():
    """
    Melakukan autentikasi dengan akun Google pengguna.
    Fungsi ini akan membuka browser untuk login saat pertama kali dijalankan.
    Setelah itu, kredensial akan disimpan di 'token.json' untuk penggunaan selanjutnya.
    """
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Gagal me-refresh token: {e}")
                print(f"Hapus file '{TOKEN_FILE}' dan jalankan ulang program.")
                return None

        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"Error: File '{CREDENTIALS_FILE}' tidak ditemukan.")
                print("Silakan unduh dari Google Cloud Console dan letakkan di folder yang sama dengan script ini.")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    try:
        return build('calendar', 'v3', credentials=creds)
    except HttpError as error:
        print(f'Terjadi error saat membangun service: {error}')
        return None


def create_event(service, event_data, use_datetime: bool = False):
    """
    Membuat satu acara baru di Google Calendar.
    Gunakan use_datetime=True untuk acara dengan waktu spesifik (dateTime),
    atau False untuk acara seharian penuh (date).
    """
    time_key = 'dateTime' if use_datetime else 'date'
    event = {
        'summary': event_data['summary'],
        'description': event_data.get('description', ''),
        'start': {time_key: event_data['start'], 'timeZone': TIMEZONE},
        'end': {time_key: event_data['end'], 'timeZone': TIMEZONE},
    }
    try:
        created = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print(f"Berhasil: '{event['summary']}' -> {created.get('htmlLink')}")
    except HttpError as error:
        print(f"Gagal membuat '{event['summary']}': {error}")


def load_events_from_file(filename: str) -> list | None:
    """
    Membaca dan memvalidasi daftar acara dari file JSON.
    Mengembalikan list acara, atau None jika terjadi error.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list) or not data:
            print(f"Error: '{filename}' tidak berisi daftar acara yang valid atau kosong.")
            return None
        return data
    except FileNotFoundError:
        print(f"Error: File '{filename}' tidak ditemukan.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Gagal mem-parsing '{filename}'. Pastikan formatnya benar.")
        return None


def insert_events(service, filename: str, use_datetime: bool = False):
    """
    Membaca acara dari file JSON dan menambahkannya ke Google Calendar.
    """
    print(f"Memuat acara dari '{filename}' ke kalender '{CALENDAR_ID}'...")
    events = load_events_from_file(filename)
    if events is None:
        return

    for event_data in events:
        create_event(service, event_data, use_datetime=use_datetime)

    print(f"\nSelesai memproses {len(events)} acara dari '{filename}'.")


def main():
    """
    Fungsi utama: autentikasi lalu tampilkan menu untuk memilih jenis acara yang akan ditambahkan.
    """
    service = authenticate_google_calendar()
    if not service:
        print("Proses dihentikan karena autentikasi gagal.")
        return

    menu = {
        '1': ("Tambahkan Kalender Akademik (events.json)",
              lambda: insert_events(service, 'events.json', use_datetime=False)),
        '2': ("Tambahkan Jadwal Mata Kuliah (matkul_events.json)",
              lambda: insert_events(service, 'matkul_events.json', use_datetime=True)),
        '3': ("Keluar", None),
    }

    while True:
        print("\n--- MENU UTAMA ---")
        for key, (label, _) in menu.items():
            print(f"{key}. {label}")

        choice = input("Masukkan pilihan Anda: ").strip()

        if choice == '3':
            print("Keluar dari program. Sampai jumpa!")
            break
        elif choice in menu:
            _, action = menu[choice]
            action()
        else:
            print("Pilihan tidak valid, silakan coba lagi.")


if __name__ == '__main__':
    main()