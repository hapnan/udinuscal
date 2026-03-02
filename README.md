# Udinus Calendar

Menambahkan kalender akademik dan jadwal mata kuliah Universitas Dian Nuswantoro (Udinus) ke Google Calendar menggunakan Python.

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (package & venv manager)
- Akun Google dengan Google Calendar API diaktifkan

## Setup Google Cloud

1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Buat project baru (atau gunakan yang sudah ada)
3. Aktifkan [**Google Calendar API**](https://console.cloud.google.com/flows/enableapi?apiid=calendar-json.googleapis.com)
4. Buat [**OAuth 2.0 Client ID**](https://developers.google.com/workspace/calendar/api/quickstart/python#configure_the_oauth_consent_screen) (tipe: *Desktop app*)
5. Authorize credentials untuk aplikasi [Dekstop](https://developers.google.com/workspace/calendar/api/quickstart/python#authorize_credentials_for_a_desktop_application)  
5. Unduh file kredensial dan simpan sebagai `credentials.json` di folder yang sama dengan `main.py`

Saat pertama kali dijalankan, browser akan terbuka untuk otorisasi akun Google Anda. Token akan disimpan otomatis di `token.json` untuk sesi berikutnya.

## Data Files

### `events.json` — Kalender Akademik (acara seharian)

Objek JSON dengan key `agenda_akademik` berisi array item. Tanggal menggunakan format `YYYY-MM-DD`. Digunakan juga sebagai sumber rentang tanggal perkuliahan untuk jadwal mata kuliah (melalui entri `Awal Perkuliahan 1 Genap`, `Akhir Perkuliahan 2 Genap`, dan `Ujian Tengah Semester Genap`).

```json
{
  "universitas": "Universitas Dian Nuswantoro",
  "tahun_akademik": "2025/2026",
  "agenda_akademik": [
    {
      "kegiatan": "Nama Kegiatan",
      "start": "2025-08-11",
      "end": "2025-08-11"
    }
  ]
}
```

### `matkul.json` — Jadwal Mata Kuliah (acara berwaktu)

Array objek mata kuliah. Hari menggunakan bahasa Indonesia kapital, waktu menggunakan titik sebagai pemisah (mis. `"15.30"`).

```json
[
  {
    "no": 1,
    "kode_mk": "A18.11401",
    "nama_mata_kuliah": "NAMA MATA KULIAH",
    "sks": 3,
    "kelompok": "A18.1401",
    "jadwal": {
      "hari": "SENIN",
      "start": "08.00",
      "end": "09.40",
      "ruang": "Kulino"
    }
  }
]
```

> Semua acara menggunakan zona waktu **Asia/Jakarta (WIB)**.

Jadwal mata kuliah otomatis melewati hari libur nasional (via [libur.deno.dev](https://libur.deno.dev)) dan periode Ujian Tengah Semester (UTS).

## Logging

Semua output ditampilkan di konsol dan disimpan ke file `udinuscal.log` dengan format:

```
YYYY-MM-DD HH:MM:SS [LEVEL] pesan
```

## Run

```sh
uv run main.py
```

## Menu

| Pilihan | Keterangan |
|---------|------------|
| `1` | Tambahkan Kalender Akademik dari `events.json` |
| `2` | Tambahkan Jadwal Mata Kuliah dari `matkul.json` |
| `3` | Keluar |