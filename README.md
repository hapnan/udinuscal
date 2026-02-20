# Udinus Calendar

Menambahkan kalender akademik dan jadwal mata kuliah Universitas Dian Nuswantoro (Udinus) ke Google Calendar menggunakan Python.

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (package & venv manager)
- Akun Google dengan Google Calendar API diaktifkan

## Setup Google Cloud

1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Buat project baru (atau gunakan yang sudah ada)
3. Aktifkan **Google Calendar API**
4. Buat **OAuth 2.0 Client ID** (tipe: *Desktop app*)
5. Unduh file kredensial dan simpan sebagai `credentials.json` di folder yang sama dengan `main.py`

Saat pertama kali dijalankan, browser akan terbuka untuk otorisasi akun Google Anda. Token akan disimpan otomatis di `token.json` untuk sesi berikutnya.

## Data Files

### `events.json` — Kalender Akademik (acara seharian)

```json
[
  {
    "summary": "Nama Acara",
    "start": "2025-08-11",
    "end": "2025-08-12",
    "description": "Deskripsi opsional"
  }
]
```

### `matkul_events.json` — Jadwal Mata Kuliah (acara berwaktu)

```json
[
  {
    "summary": "Nama Mata Kuliah",
    "start": "2025-09-01T08:00:00",
    "end": "2025-09-01T09:40:00",
    "description": "Deskripsi opsional"
  }
]
```

> Semua acara menggunakan zona waktu **Asia/Jakarta (WIB)**.

## Run

```sh
uv run main.py
```

## Menu

| Pilihan | Keterangan |
|---------|------------|
| `1` | Tambahkan Kalender Akademik dari `events.json` |
| `2` | Tambahkan Jadwal Mata Kuliah dari `matkul_events.json` |
| `3` | Keluar |