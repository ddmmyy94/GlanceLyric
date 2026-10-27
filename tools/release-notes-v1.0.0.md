# GlanceLyric v1.0 — Uji awal

**Pre-release untuk pengujian awal Windows.** Pemilik berencana mencoba paket
ini pada komputer rekan kantor setelah publikasi. Pengujian instalasi, upgrade,
uninstall, autostart saat login, dan pemutaran Spotify langsung belum selesai.

## Windows x64 dan Spotify desktop

GlanceLyric menampilkan dua baris lirik tersinkronisasi pada taskbar Windows.
Anda dapat mengatur font, warna, tema, transparansi, dan offset lirik. Watcher
autostart bersifat opsional. Kode aplikasi memakai lisensi MIT; download,
instalasi, dan penggunaan tidak memerlukan donasi.

Persyaratan: Windows 10 versi 1809 atau lebih baru, atau Windows 11 pada
perangkat x64; Spotify desktop; internet untuk mengambil lirik yang belum ada
di cache. Paket menyertakan runtime, sehingga Python dan SpotX tidak diperlukan.

## Instalasi

- Installer: jalankan `GlanceLyric-Setup-1.0.0-x64.exe`. Installer memasang per-user
  tanpa Administrator dan menawarkan pilihan desktop shortcut serta autostart.
- Portable: ekstrak `GlanceLyric-v1.0-windows-x64.zip`, lalu jalankan
  `GlanceLyric/GlanceLyric.exe`. Pertahankan folder `_internal` di sampingnya.
- Putar lagu di Spotify desktop. Klik kanan widget untuk membuka Settings.
- Untuk menghapus edisi installer, gunakan Windows Settings → Apps. Nonaktifkan
  autostart dan tutup proses sebelum menghapus edisi portable. Kedua cara
  mempertahankan data lokal di `%USERPROFILE%\.glancelyric`.

Executable belum ditandatangani (unsigned); Windows dapat menampilkan peringatan
unknown publisher atau SmartScreen. Bandingkan SHA-256 installer dan ZIP dengan
`SHA256SUMS.txt` dari release sebelum menjalankannya.

## Batasan

- Spotify di browser belum didukung.
- Ketersediaan dan ketepatan lirik bergantung pada LRCLIB serta metadata lagu.
- WinGet masih planned, bukan metode instalasi yang sudah tersedia.
- Tidak ada auto-update atau pemroses pembayaran di dalam aplikasi.

## Status validasi

- Build installer dan ZIP, tes otomatis aplikasi, serta pemeriksaan hash,
  integritas ZIP, notice, dan aset README telah lulus pada persiapan lokal.
- Pemeriksaan runtime executable dari ZIP berhasil membuka komponen UI dan
  terhubung ke Windows media session. Ini bukan uji Spotify live atau instalasi.
- Pengujian manual Windows menyusul publikasi. Harap laporkan versi Windows,
  versi Spotify, langkah reproduksi, dan pesan error jika menemukan masalah.
- Unduh `SHA256SUMS.txt` bersama paket dan cocokkan SHA-256 sebelum menjalankan.

## Dukungan sukarela

[Dukung GlanceLyric melalui SociaBuzz](https://sociabuzz.com/ddmmyy94/tribe).
Donasi tidak menjadi syarat download, instalasi, atau penggunaan. Pemroses
pembayaran berada di situs SociaBuzz, bukan dalam aplikasi.
