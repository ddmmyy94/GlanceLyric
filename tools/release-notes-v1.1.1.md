# GlanceLyric v1.1.1

## Perbaikan

- **Notifikasi update saat login Windows.** Watcher memeriksa GitHub tanpa
  menunggu Spotify atau widget terbuka. Dialog menampilkan versi terpasang,
  versi terbaru, dan catatan rilis yang bisa digulir.
- **Download, Not Now, Skip This Version.** Download membuka halaman rilis
  resmi. Not Now menunda sampai sesi watcher login berikutnya; Skip This Version
  melewati versi tersebut tanpa memblokir versi yang lebih baru.
- **Autostart.** Installer baru mencentang Start with Windows. Pilihan upgrade
  sebelumnya tetap berlaku. Anda juga bisa mengaktifkannya dari Settings atau
  `GlanceLyric.exe --install`; perintah ini langsung menjalankan watcher.
  Watcher mencoba lagi jika proses widget gagal berjalan, dan tetap menghormati Exit.
- **Timing lirik.** Clock memakai waktu monotonic untuk snapshot Spotify yang
  belum berubah, tidak menghitung waktu pause saat resume, dan mengabaikan
  timestamp tidak masuk akal. GlanceLyric mengutamakan sesi Spotify yang playing.
  Lookup dan cache memeriksa identitas serta durasi agar rekaman berbeda tidak
  memakai lirik yang salah. Gunakan + / − untuk selisih timing pada sumber lirik.
- **Support this Project** tersedia di menu klik kanan dan membuka
  https://sociabuzz.com/ddmmyy94/tribe di browser.

## Syarat notifikasi

Aktifkan **Start with Windows** dan pemeriksaan update di Settings. Pastikan
Windows mengizinkan GlanceLyric di Settings → Apps → Startup. Pemeriksaan mulai
setelah login dan membutuhkan internet. Sesudah pemeriksaan sukses, aplikasi
menunggu satu jam; saat login watcher melakukan pemeriksaan baru. Jika offline,
aplikasi mencoba lagi setiap lima menit selama masih berjalan. Aplikasi tidak
menampilkan popup jika tidak ada versi lebih baru, dan tidak memasang update sendiri.

Pengguna v1.1.0 menerima pemberitahuan melalui widget lama yang terbuka, sesuai
jeda pemeriksaan lamanya. Pengguna v1.0 belum punya checker dan perlu mengunduh
pembaruan secara manual. Kami tidak bisa menambahkan fitur ke executable yang
sudah terpasang tanpa pembaruan. Untuk ZIP portable, aktifkan startup dari Settings.

## Pengujian

Tes otomatis mencakup dialog tanpa Spotify, lock notifikasi bersama, kondisi
offline, skip/later, pause/resume/seek, kecocokan rekaman, menu dukungan, dan
layout taskbar. Login/reboot, upgrade/uninstall installer, dan Spotify pada PC
lain tetap memerlukan uji manual. Rilis ini tetap ditujukan untuk pengujian awal.

Download dan penggunaan gratis. Dukungan SociaBuzz bersifat opsional.
