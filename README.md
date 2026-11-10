# Tugas 2 Komputasi Berbasis Jaringan — Celery Message Brokering

**Kelompok:** Laura Naily Tsabita (26051905009) dan Teguh Arifianto (26051905011)  
**Program Studi:** Magister Informatika, Universitas Negeri Surabaya  
**Tahun:** 2026

## Ruang lingkup

Contoh **job queue** dengan **Celery worker**, **RabbitMQ broker**, **Redis result backend**, dan **Flower monitor**. Menguji fan-out, topic, dan wildcard routing dengan producer pembangkit data sensor serta tugas pemrosesan data sederhana.

> Catatan akademik: Kode UTS asli belum disediakan. Fungsi `transform_event` adalah **contoh integrasi** yang dapat diganti dengan logika program UTS asli, bukan klaim bahwa program UTS telah dimodifikasi.

## Arsitektur

```text
producer.py -> RabbitMQ exchange -> RabbitMQ queue(s) -> Celery worker(s)
                                                |               |
                                                |            Redis result
                                                +-> output/*.json (audit)
Flower <---------- Celery broker/events
```

## Cara menjalankan (Docker Desktop diperlukan)

```bash
docker compose up -d --build rabbitmq redis worker flower
docker compose --profile manual run --rm producer python producer.py --scenario all --count 8 --interval 0.1
```

Untuk skenario terpisah:

```bash
docker compose --profile manual run --rm producer python producer.py --scenario fanout --count 8
docker compose --profile manual run --rm producer python producer.py --scenario topic --count 8
docker compose --profile manual run --rm producer python producer.py --scenario wildcard --count 8
```

Lihat hasil: `output/*.json`, `docker compose logs -f worker`, Flower di http://localhost:5555 dan RabbitMQ UI di http://localhost:15672 (`kbj` / `kbj2026`, **hanya untuk pengembangan lokal**).

Berhenti: `docker compose down`. Bersihkan hasil antar-skenario: hapus file `.json` di `output/` sebelum menguji ulang.

## Alternatif venv (broker RabbitMQ dan Redis harus sudah berjalan)

```bash
python -m venv myenv
# Windows PowerShell: .\\myenv\\Scripts\\Activate.ps1
# Linux/macOS: source myenv/bin/activate
pip install -r requirements.txt
# Atur CELERY_BROKER_URL dan CELERY_RESULT_BACKEND sesuai broker lokal
celery -A app.celery_app:app worker -l INFO -E -Q fanout_a,fanout_b,topic_sensor,topic_system,wildcard_single,wildcard_multi
python producer.py --scenario all --count 8
```

Jalankan tests: `pytest -q` (perlu dependensi terinstal). Log routing lengkap dapat dilihat melalui UI RabbitMQ bagian Exchanges / Queues.

## Perbedaan skenario

| Skema | Exchange | Binding | Hasil yang diharapkan |
|---|---|---|---|
| Fan-Out | `kbj.fanout`, `fanout` | `fanout_a`, `fanout_b` | Setiap pesan dikirim ke kedua queue, routing key diabaikan |
| Topic | `kbj.topic`, `topic` | `sensor.*` dan `system.#` | `sensor.temperature` cocok `sensor.*`; `system.warning.disk` cocok `system.#`; `other.misc` tidak cocok |
| Wildcard | `kbj.wildcard`, `topic` | `sensor.*.critical` dan `sensor.#` | `sensor.room.critical` cocok kedua binding; `sensor.critical` hanya cocok `sensor.#`; `sensor.room.floor.critical` hanya cocok `sensor.#` |

**Penting:** wildcard bukan tipe exchange terpisah di RabbitMQ; `*` (tepat satu segmen) dan `#` (nol atau lebih segmen) adalah pola binding untuk **topic exchange**. Jika pesan cocok ke dua queue, masing-masing menerima salinan pesan. Satu queue dengan banyak worker tetap diproses oleh satu worker per pesan.

## Hubungkan ke program UTS asli

Ganti isi `transform_event()` pada `app/tasks.py` dengan proses inti program UTS, pastikan argumen bisa diserialisasi ke JSON. Jika UTS menggunakan API atau basis data, konfigurasi dependensinya kemudian jalankan proses berat sebagai Celery task. Lakukan pengujian ulang end-to-end menggunakan data UTS asli dan catat hasilnya.

## Dokumentasi

Lihat [`docs/LAPORAN.md`](docs/LAPORAN.md) untuk uraian tugas, skenario uji, interpretasi, dan daftar bukti yang perlu direkam. Tidak ada screenshot maupun hasil eksekusi broker yang direkayasa.

## Unggah ke GitHub

```bash
git init
git add .
git commit -m "Tugas KBJ Celery routing fanout topic wildcard"
git branch -M main
git remote add origin https://github.com/USERNAME/NAMA-REPO.git
git push -u origin main
```

Buat repo kosong di GitHub terlebih dahulu. Ganti `USERNAME/NAMA-REPO` dengan alamat repo milik kelompok. **Tiap mahasiswa memasukkan URL repo yang sama di Google Form/Classroom sesuai instruksi dosen.**
