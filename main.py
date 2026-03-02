import os.path
import json
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow # type: ignore
from googleapiclient.discovery import build, Resource # type: ignore
from googleapiclient.errors import HttpError
from collections.abc import Iterator
from datetime import datetime, timedelta
import requests
# Jika Anda mengubah cakupan (scopes) ini, hapus file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
TIMEZONE = 'Asia/Jakarta'
CALENDAR_ID = 'primary'
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'
LOG_FILE = 'udinuscal.log'

# Setup logging to both console and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(),
    ]
)

logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


def authenticate_google_calendar():
    """
    Melakukan autentikasi dengan akun Google pengguna.
    Fungsi ini akan membuka browser untuk login saat pertama kali dijalankan.
    Setelah itu, kredensial akan disimpan di 'token.json' untuk penggunaan selanjutnya.
    """
    creds: Credentials | None = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Gagal me-refresh token: {e}")
                logger.info(f"Hapus file '{TOKEN_FILE}' dan jalankan ulang program.")
                return None

        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                logger.error(f"Error: File '{CREDENTIALS_FILE}' tidak ditemukan.")
                logger.info("Silakan unduh dari Google Cloud Console dan letakkan di folder yang sama dengan script ini.")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    try:
        return build('calendar', 'v3', credentials=creds)
    except HttpError as error:
        logger.error(f'Terjadi error saat membangun service: {error}')
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
        logger.info(f"Berhasil: '{event['summary']}' -> {created.get('htmlLink')}")
    except HttpError as error:
        logger.error(f"Gagal membuat '{event['summary']}': {error}")


def load_events_from_file(filename: str) -> list | None:
    """
    Membaca dan memvalidasi daftar acara dari file JSON.
    Mengembalikan list acara, atau None jika terjadi error.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list) or not data:
            logger.error(f"Error: '{filename}' tidak berisi daftar acara yang valid atau kosong.")
            return None
        return data
    except FileNotFoundError:
        logger.error(f"Error: File '{filename}' tidak ditemukan.")
        return None
    except json.JSONDecodeError:
        logger.error(f"Error: Gagal mem-parsing '{filename}'. Pastikan formatnya benar.")
        return None


def daterange(start_date: datetime, end_date: datetime) -> Iterator[datetime]:
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(days=n)

def insert_events(service, filename: str, use_datetime: bool = False):
    """
    Membaca acara dari file JSON dan menambahkannya ke Google Calendar.
    """
    logger.info(f"Memuat acara dari '{filename}' ke kalender '{CALENDAR_ID}'...")

    if use_datetime == False:
        # events.json: objek dengan key 'agenda_akademik', tiap item pakai 'kegiatan' bukan 'summary'
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Error: File '{filename}' tidak ditemukan.")
            return
        except json.JSONDecodeError:
            logger.error(f"Error: Gagal mem-parsing '{filename}'. Pastikan formatnya benar.")
            return

        agenda = data.get('agenda_akademik', [])
        if not agenda:
            logger.error(f"Error: '{filename}' tidak berisi agenda yang valid atau kosong.")
            return

        logger.info("Tipe acara: Seharian penuh (date)")
        for item in agenda:
            if item['start'] == item['end']:
                event_data = {
                    'summary': item['kegiatan'],
                    'start': item['start'],
                    'end': item['end'],
                }
            else:
                event_data = {
                    'summary': item['kegiatan'],
                    'start': item['start'],
                    'end': (datetime.strptime(item['end'], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
                }
            create_event(service, event_data, use_datetime=False)
        logger.info(f"Selesai memproses {len(agenda)} acara dari '{filename}'.")
    else:
        # matkul.json: array objek dengan 'nama_mata_kuliah' dan nested 'jadwal'
        # dengan hari dalam bahasa Indonesia dan waktu pakai titik (e.g. "15.30")
        events = load_events_from_file(filename)
        if events is None:
            return

        day_map = {
            'SENIN': 'Monday', 'SELASA': 'Tuesday', 'RABU': 'Wednesday',
            'KAMIS': 'Thursday', 'JUMAT': 'Friday', 'SABTU': 'Saturday', 'MINGGU': 'Sunday',
        }

        # Ambil rentang tanggal perkuliahan dari events.json (format baru)
        try:
            with open('events.json', 'r', encoding='utf-8') as f:
                cal_data = json.load(f)
            agenda = cal_data.get('agenda_akademik', [])
            start_str = next((i['start'] for i in agenda if i['kegiatan'] == 'Awal Perkuliahan 1 Genap'), None)
            end_str = next((i['start'] for i in agenda if i['kegiatan'] == 'Akhir Perkuliahan 2 Genap'), None)
            uts_start = next((i['start'] for i in agenda if i['kegiatan'] == 'Ujian Tengah Semester Genap'), None)
            uts_end = next((i['end'] for i in agenda if i['kegiatan'] == 'Ujian Tengah Semester Genap'), None)
        except Exception as e:
            logger.error(f"Error membaca 'events.json': {e}")
            return

        if not start_str or not end_str:
            logger.error("Error: Tidak dapat menemukan tanggal perkuliahan di 'events.json'.")
            return

        start_date: datetime = datetime.strptime(start_str, "%Y-%m-%d")
        end_date: datetime = datetime.strptime(end_str, "%Y-%m-%d")
        logger.info("Tipe acara: Waktu spesifik (dateTime)")
        logger.info(f"Rentang perkuliahan: {start_date.date()} s/d {end_date.date()}")

        for single_date in daterange(start_date, end_date):
            day_en = single_date.strftime("%A")
            try:
                response = requests.get(f"https://libur.deno.dev/api?year={single_date.year}&month={single_date.month}&day={single_date.day}")
                if response.status_code == 200 and response.json().get("is_holiday", False):
                    logger.info(f"Melewatkan hari libur: {single_date.strftime('%Y-%m-%d')}")
                    continue
                elif single_date.strftime("%Y-%m-%d") >= uts_start and single_date.strftime("%Y-%m-%d") <= uts_end:
                    logger.info(f"Melewatkan UTS: {single_date.strftime('%Y-%m-%d')}")
                    continue
            except requests.RequestException as e:
                logger.warning(f"Peringatan: Gagal mengecek hari libur untuk {single_date.strftime('%Y-%m-%d')}: {e}")


            for matkul in events:
                jadwal = matkul['jadwal']
                if day_map.get(jadwal['hari'], '') == day_en:
                    start_time_str = jadwal['start'].replace('.', ':')
                    end_time_str = jadwal['end'].replace('.', ':')
                    start_matkul = datetime.combine(single_date, datetime.strptime(start_time_str, "%H:%M").time())
                    end_matkul = datetime.combine(single_date, datetime.strptime(end_time_str, "%H:%M").time())
                    event_data = {
                        'summary': matkul['nama_mata_kuliah'],
                        'description': matkul.get('kode_mk', ''),
                        'start': start_matkul.isoformat(),
                        'end': end_matkul.isoformat(),
                    }
                    create_event(service, event_data, use_datetime=True)
        logger.info(f"Selesai memproses {len(events)} mata kuliah dari '{filename}'.")


def main():
    """
    Fungsi utama: autentikasi lalu tampilkan menu untuk memilih jenis acara yang akan ditambahkan.
    """
    service = authenticate_google_calendar()

    if not service:
        logger.error("Proses dihentikan karena autentikasi gagal.")
        return

    menu = {
        '1': ("Tambahkan Kalender Akademik (events.json)",
              lambda: insert_events(service, 'events.json', use_datetime=False)),
        '2': ("Tambahkan Jadwal Mata Kuliah (matkul.json)",
              lambda: insert_events(service, 'matkul.json', use_datetime=True)),
        '3': ("Keluar", None),
    }

    while True:
        print("--- MENU UTAMA ---")
        for key, (label, _) in menu.items():
            print(f"{key}. {label}")

        choice = input("Masukkan pilihan Anda: ").strip()

        if choice == '3':
            logger.info("Keluar dari program. Sampai jumpa!")
            break
        elif choice in menu:
            _, action = menu[choice]
            action()
        else:
            logger.warning(f"Pilihan tidak valid: '{choice}'")


if __name__ == '__main__':
    main()