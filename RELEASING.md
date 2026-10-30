# Publikasi GlanceLyric

Repository tujuan yang dikonfirmasi pemilik: `https://github.com/ddmmyy94/GlanceLyric`.

## v1.1.0, 30 Oktober 2026

Source lokal sekarang memakai versi `1.1.0` pada UI, metadata executable, dan
installer. `tools/build.py` mengambil versi untuk nama ZIP/installer dari
`glance_backend.APP_VERSION`. Pemilik menyetujui publikasi setelah mengonfirmasi
uji langsung Spotify dan pergantian mode taskbar pada perangkatnya. Rilis tetap
**pre-release** karena validasi installer dan perangkat lain belum selesai.
Paket uji lokal di `output/taskbar-v1.1.0-test-2026-10-30/candidate/dist` bukan
paket publikasi final. Jangan mengganti aset v1.0.0.

- Catatan rilis: `tools/release-notes-v1.1.0.md`.
- Perbaikan: widget mengecilkan font untuk mengikuti tinggi taskbar horizontal
  dan mengembalikan ukuran sesuai ruang yang tersedia tanpa mengubah preferensi.
- Pemeriksa update: GitHub Releases setelah widget dibuka, request pada worker, throttle sukses 24 jam,
  pengulangan pemeriksaan gagal pada startup/timer per jam, dan satu notifikasi
  per versi. Menu **Check for updates…** mengabaikan throttle dan bisa membuka
  catatan yang sudah pernah ditutup. Settings menyediakan pilihan menonaktifkan
  pemeriksaan otomatis; notifikasi tidak mengunduh/menjalankan paket.
- `APP_PRERELEASE = True` mempertahankan kanal uji awal. Publikasikan tag numerik
  `vMAJOR.MINOR.PATCH` dan tandai pre-release melalui GitHub, bukan suffix tag.
  Source memeriksa 100 rilis terbaru dan memilih versi numerik tertinggi yang
  memiliki installer atau ZIP berstatus uploaded. Draft dan rilis tanpa paket
  tidak memicu notifikasi. Untuk rilis stabil kelak, set `APP_PRERELEASE = False`.
- Isi body GitHub Release menjadi catatan dalam dialog. UI menampilkannya sebagai
  teks biasa; link download selalu menuju repository resmi, bukan URL dari body.
- Pengguna v1.0 perlu memasang v1.1.0 secara manual sekali. Tidak ada mekanisme
  pada binary v1.0 yang bisa menerima fitur update checker dari jarak jauh.
- Watcher login belum memeriksa update sendiri. Jika widget belum terbuka,
  tidak ada popup hanya karena laptop baru login. Jelaskan batasan ini saat
  mengumumkan pembaruan; jangan menjanjikan notifikasi jarak jauh untuk v1.0.

Jalankan `python test_glance.py`, `python test_updates.py`, dan
`python test_taskbar.py`. Tes memakai fixture untuk update dan pengukuran mode
taskbar; tidak mengubah taskbar Windows. `test_taskbar.py` mencakup 144 kombinasi
per skala aplikasi dan menerima folder bukti sebagai argumen. Variasikan
`QT_SCALE_FACTOR=1`, `1.25`, dan `1.5` pada proses uji, bukan pengaturan OS.
Dialog catatan panjang juga diuji setelah diperluas agar tetap di dalam layar.
Jalankan `python test_release.py`
setelah build **v1.1.0** selesai; tes paket tidak berlaku untuk dist v1.0 yang
masih ada. Pertahankan AppId Inno Setup agar installer mengenali aplikasi lama.

Uji langsung Spotify dan perubahan ukuran taskbar mendapat konfirmasi pemilik.
Tes otomatis mencakup 432 kombinasi pada skala aplikasi 100/125/150%, enam posisi
executable pada taskbar nyata, dan pemeriksaan GitHub otomatis dari executable.
Uji manual installer/upgrade/uninstall/login autostart, DPI OS, Windows 10, dan
komputer lain belum selesai. Catat batasan ini pada body release.

Publikasi v1.1.0:

1. Periksa source/secret, commit pada branch perubahan, lalu merge melalui PR.
   Pertahankan identitas pemilik; jangan menambahkan trailer atribusi otomatis.
2. Bangun dari commit final yang bersih pada worktree terpisah. Jangan menimpa
   executable paket uji yang sedang dipakai pemilik atau aset v1.0.0.
3. Jalankan tes source, `test_release.py`, dan runtime executable dari ZIP hasil
   ekstraksi. Tag `v1.1.0` harus menunjuk commit build yang sama.
4. Buat draft pre-release dengan installer `GlanceLyric-Setup-1.1.0-x64.exe`,
   ZIP `GlanceLyric-v1.1.0-windows-x64.zip`, dan `SHA256SUMS.txt`, lalu publikasikan.
5. Unduh ketiga aset tanpa autentikasi dan cocokkan hash dengan build lokal.
   Gunakan URL `/releases/tag/v1.1.0`, bukan `/releases/latest` untuk pre-release.
6. Setelah verifikasi, perbarui website dan pengumuman upgrade v1.0. Backup HTML
   di luar web root dan pertahankan CSS/JS/statistik serta konfigurasi yang aktif.

## Catatan rilis awal v1.0.0

Versi aplikasi di UI: `v1.0`; versi paket installer: `1.0.0`.
Metadata file: `1.0.0.0`; kandidat tag: `v1.0.0`. Perbedaan format ini disengaja;
tidak perlu menaikkan versi untuk publikasi awal.
Calon ID WinGet: `ddmmyy94.GlanceLyric`.

## Status publikasi, 27 Oktober 2026

- Pemilik mengonfirmasi akun GitHub `ddmmyy94` dan mengizinkan publikasi source
  serta rilis awal. Repository publik sudah dibuat di bawah akun tersebut dan
  autentikasi pemilik sudah diverifikasi. Pre-release memakai URL tag langsung;
  `/releases/latest` tidak mewakili pre-release ini.
- Git lokal memakai branch `main`. Tag rilis harus menunjuk commit source
  bersih yang dipakai untuk build; periksa akses publik assets setelah upload.
- Situs resmi aktif di https://ggdealstore.site/glancelyric. Halaman masih
  menyatakan persiapan rilis dan belum menyediakan unduhan publik.
- Pemilik memberikan https://sociabuzz.com/ddmmyy94/tribe. Halaman publik
  menampilkan identitas Ddmmyy94 dan tombol Beri Dukungan. `.github/FUNDING.yml`
  memakai `custom` untuk URL ini; README dan website memakai tujuan yang sama.
  GitHub Sponsors tidak dikonfigurasi. Midtrans masih menunggu aktivasi.
- Pemilik memilih pengujian manual pada komputer Windows rekan kantor setelah
  go public. Publikasikan rilis awal sebagai **pre-release**, nyatakan pengujian
  manual belum dilakukan, dan jangan mengklaim instalasi/upgrade/uninstall atau
  Spotify live sudah lulus. Build dan tes otomatis tetap dijalankan.
- `.env` beserta variannya, environment lokal, secret, dan bahan merchant tidak
  boleh masuk staging, history publik, ataupun assets rilis. Periksa ulang
  sebelum setiap push. Gunakan identitas commit pemilik tanpa trailer otomatis.

## 1. Build dan uji

Pasang Inno Setup 6.3 atau lebih baru, lalu jalankan dari root proyek:

```powershell
.\Build.bat
.\.venv\Scripts\python.exe test_glance.py
.\.venv\Scripts\python.exe test_release.py
```

Hasil yang akan diunggah sebagai release assets:

- `dist/GlanceLyric-Setup-1.0.0-x64.exe`
- `dist/GlanceLyric-v1.0-windows-x64.zip`
- `dist/SHA256SUMS.txt` (hash kedua paket, dibuat otomatis oleh build)

`test_release.py` memeriksa kedua hash, integritas ZIP, notice lisensi, serta
tautan aset README di paket. Jalankan setelah build lengkap, termasuk installer.
Tes ini tidak menggantikan uji instalasi atau verifikasi unduhan publik.

Untuk validasi manual setelah pre-release publik, uji instalasi, upgrade dengan
installer yang sama, dan uninstall pada komputer Windows uji. Periksa Start
Menu, Settings, Spotify desktop, dan autostart. Pemilik berencana menguji pada
komputer rekan kantor; catat izin dan hasil tiap perangkat. Untuk silent install
di akun uji, gunakan:

```powershell
Start-Process .\dist\GlanceLyric-Setup-1.0.0-x64.exe -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-' -Wait
```

Silent install tidak membuka aplikasi atau memilih task autostart secara default.
Installer memasang per-user ke `%LOCALAPPDATA%\Programs\GlanceLyric` dan
mendaftarkan uninstaller pada Windows. Tutup widget serta watcher sebelum
uninstall agar seluruh file dapat dihapus.

Logo sumber ada di `assets/glancelyric.png`; build tidak menimpa file tersebut.
Untuk rilis berikutnya, samakan versi di `glance_backend.py`,
`tools/version_info.txt`, `tools/installer.iss`, dan nama ZIP pada `tools/build.py`.
Sesuaikan juga pemeriksaan versi di `glancelyric.pyw` dan dokumentasi.

## 2. Periksa source, lalu buat repository dan GitHub Release

1. Konfirmasi owner dan repository dengan pemilik. Periksa `git status`, root,
   remote, dan history jika ada. Inisialisasi Git hanya di root aplikasi bila
   diperlukan; jangan mengganti remote atau force-push.
2. Periksa file calon source dengan `git add --dry-run .`. `.gitignore`
   mengecualikan `.venv/`, `build/`, `dist/`, `output/`, `tmp/`, salinan installer
   uji, `.env`, secret, dan log. Periksa data pribadi, kredensial, serta file besar
   sebelum staging; ulangi pemeriksaan pada `git diff --cached --stat` dan
   `git diff --cached`. Jangan unggah PDF merchant atau paket biner sebagai source.
3. Sertakan source, `assets/`, `tools/`, tes, dokumentasi, serta notice lisensi.
   README memakai screenshot aplikasi dengan lirik contoh, bukan bukti pemutaran
   Spotify. Jangan mengubah ilustrasi website menjadi klaim screenshot asli.
4. Bootstrap default branch pada repository yang sudah dikonfirmasi. Setelah
   baseline tersedia, gunakan branch perubahan dan PR sesuai aturan repository.
   Tidak ada PR sebelum remote dan branch dasar tersedia.
5. Bangun paket dari commit source final yang bersih. Catat commit tersebut dan
   hasil pengujian, lalu arahkan tag **`v1.0.0`** ke commit yang sama. Jangan
   menandai commit lain atau mengunggah paket lama setelah source berubah.
6. Buat **draft pre-release** berjudul **GlanceLyric v1.0 — Uji awal**. Gunakan
   `tools/release-notes-v1.0.0.md` dengan status tes otomatis dan pengujian manual.
   Lampirkan kedua paket dan `SHA256SUMS.txt`, periksa assets, lalu publikasikan
   setelah tes otomatis lulus dan akses/izin tersedia. Uji Windows manual
   menyusul publikasi sesuai keputusan pemilik, bukan ditandai lulus.
7. Hitung hash kedua file sebelum mengunggah:

```powershell
Get-FileHash .\dist\GlanceLyric-Setup-1.0.0-x64.exe -Algorithm SHA256
Get-FileHash .\dist\GlanceLyric-v1.0-windows-x64.zip -Algorithm SHA256
```

8. Setelah publikasi, unduh kembali installer, ZIP, dan `SHA256SUMS.txt` tanpa
   login ke folder uji. Bandingkan hash unduhan dengan checksum lokal dan publik;
   keberadaan nama asset saja belum cukup. Periksa bahwa tag menunjuk commit
   sumber build.
9. Tambahkan tautan repository, issues, badge release, dan unduhan ke README
   setelah masing-masing URL dapat diakses publik. Pre-release memakai URL
   `/releases/tag/v1.0.0` dan assets tag tersebut, bukan `/releases/latest`.
   Isi Website/About repository
   dengan `https://ggdealstore.site/glancelyric` bila akses tersedia.

URL berikut hanya kandidat, **belum menjadi tautan unduhan aktif**:

```text
https://github.com/ddmmyy94/GlanceLyric/releases/download/v1.0.0/GlanceLyric-Setup-1.0.0-x64.exe
```

Jangan mengganti isi installer untuk versi yang sudah masuk WinGet. Gunakan
versi baru agar URL, hash, dan manifest tetap konsisten.

## 3. WinGet (planned, pengajuan di luar pekerjaan publikasi awal)

Perintah `winget install --id ...` baru bekerja setelah manifest diterima di
[microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs) dan tersedia
di indeks sumber WinGet. Mengunggah source atau membuat release saja belum cukup.

Pasang Manifest Creator, lalu buat manifest dari URL release yang sudah aktif:

```powershell
winget install --id Microsoft.WingetCreate --exact --source winget
wingetcreate new https://github.com/ddmmyy94/GlanceLyric/releases/download/v1.0.0/GlanceLyric-Setup-1.0.0-x64.exe
```

Gunakan nilai berikut ketika mengisi atau memeriksa manifest:

| Field | Nilai |
| --- | --- |
| PackageIdentifier | `ddmmyy94.GlanceLyric` |
| PackageVersion | `1.0.0` |
| Publisher | `ddmmyy94` |
| PackageName | `GlanceLyric` |
| License | `MIT` |
| InstallerType | `inno` |
| Scope | `user` |
| Architecture | `x64` |
| MinimumOSVersion | `10.0.17763.0` |
| PackageUrl | `https://github.com/ddmmyy94/GlanceLyric` |
| LicenseUrl | `https://github.com/ddmmyy94/GlanceLyric/blob/main/LICENSE` (sesuaikan branch) |

Biarkan WingetCreate menghitung `InstallerSha256` dari file publik. Periksa juga
AppsAndFeaturesEntries/ProductCode yang dideteksi dari installer. Pertahankan
AppId Inno Setup yang sama untuk rilis berikutnya. Validasi dan uji manifest
sesuai [panduan resmi](https://learn.microsoft.com/windows/package-manager/package/).
Jika menguji manifest lokal, aktifkan local manifests sesuai panduan tersebut.

```powershell
winget validate --manifest .\manifests\d\ddmmyy94\GlanceLyric\1.0.0
winget install --manifest .\manifests\d\ddmmyy94\GlanceLyric\1.0.0
wingetcreate submit .\manifests\d\ddmmyy94\GlanceLyric\1.0.0
```

Sesuaikan path dengan output WingetCreate. Ikuti autentikasi GitHub yang diminta
tool, lalu pantau pull request dan pemeriksaan otomatis. Setelah diterima dan
terindeks, cek:

```powershell
winget source update
winget show --id ddmmyy94.GlanceLyric --exact --source winget
winget install --id ddmmyy94.GlanceLyric --exact --source winget
```

Setelah berhasil, ubah bagian README dari **WinGet (planned)** menjadi **WinGet**.

## 4. Aktifkan donasi

URL dukungan dari pemilik: https://sociabuzz.com/ddmmyy94/tribe. Pemeriksaan
browser menampilkan identitas Ddmmyy94 dan tombol **Beri Dukungan**. Pemeriksaan
ini tidak mencakup transaksi atau pencairan dana; pemilik menangani akun/payout.

1. `.github/FUNDING.yml` memakai `custom` dengan URL SociaBuzz di atas. Jangan
   menambahkan Buy Me a Coffee atau GitHub Sponsors berdasarkan tebakan username.
2. Field `github` hanya untuk penerima GitHub Sponsors aktif. Jika pemilik
   menyediakan platform tambahan kemudian, periksa identitas dan URL sebelum
   menambahkannya. Midtrans masih dalam aktivasi dan tidak ditautkan sekarang.
3. Masukkan konfigurasi ke default branch. Admin mengaktifkan
   **Settings → General → Features → Sponsorships**, lalu memeriksa tombol Sponsor.
4. Gunakan tujuan dukungan yang sama di README dan `glancelyric.html`. Pakai
   link biasa dengan gaya yang sudah ada, label jelas, dan `rel="noopener"`
   jika membuka tab baru. Nyatakan bahwa donasi opsional, bukan syarat download,
   instalasi, atau penggunaan. Star, issue, dan kontribusi kode tetap dapat membantu.

Pekerjaan ini tidak membuat checkout, backend pembayaran, atau integrasi
Midtrans/QRIS. Donasi eksternal tidak mengubah status verifikasi merchant maupun
checkout jasa GG Deal Store. Jangan menyimpan kredensial pembayaran di source,
README, executable, atau folder website publik.

## 5. Hubungkan website setelah rilis publik

- Perlakukan source website sebagai proyek terpisah. Konfirmasi repository dan
  branch website; jangan menginisialisasi Git pada direktori induknya.
- Aktifkan link source setelah repository publik dapat diakses tanpa login.
  Aktifkan **Download untuk Windows** hanya setelah release beserta installer,
  ZIP, dan checksum dapat diunduh dan diverifikasi. `/releases/latest` hanya
  boleh dipakai setelah mengarah ke rilis publik yang sesuai.
- Selaraskan `index.html`, `apps.html`, `glancelyric.html`, `docs.html`,
  `APPLICATIONS.md`, dan `ARCHITECTURE.md`. Selama release belum publik,
  pertahankan status persiapan tanpa tombol unduhan rusak. Simpan pending donasi
  di dokumentasi pengembang, tanpa tombol donasi aktif.
- Urutan publikasi: source dan rilis aplikasi dahulu, lalu tautan website.
  Bila kedua proyek memakai GitHub, buat PR terpisah yang saling merujuk sesuai
  alurnya. Baca `DEPLOYMENT.md`, periksa konfigurasi hosting aktual, dan deploy
  hanya file publik yang diperlukan. Jangan membuat polling API atau dependency.
- Periksa desktop/mobile, fokus keyboard, label link, dan keamanan tab baru.
  Jangan mengubah jasa, harga, Swara, atau status integrasi Midtrans.

## 6. Lisensi

MIT mengizinkan penggunaan pribadi/komersial, modifikasi, distribusi, dan penjualan
ulang dengan mempertahankan notice copyright serta lisensi. Donasi boleh.
MIT tidak mewajibkan pembuat turunan membagikan kode sumbernya. GPLv3 berbeda:
distribusi turunan harus memenuhi ketentuan GPL, termasuk penyediaan source.

LICENSE menambahkan identitas `ddmmyy94` dan mempertahankan notice workspace asal
yang sudah ada. Notice tersebut bukan klaim bahwa GlanceLyric adalah produk
resmi upstream SpotX. Lisensi dependency berlaku terpisah; build mengumpulkan
notice tersedia dalam `licenses/`. Rincian Qt/PySide6 ada di `THIRD-PARTY.md`.
