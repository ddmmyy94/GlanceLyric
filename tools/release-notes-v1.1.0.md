# GlanceLyric v1.1.0: taskbar small dan notifikasi update

**Pre-release Windows x64.** Pemilik mengonfirmasi tampilan lirik Spotify dan
pergantian ukuran taskbar pada perangkat Windows-nya pada 30 Oktober 2026.
Pengujian installer dan perangkat Windows lain masih berlanjut.

## Perbaikan taskbar small

- Dua baris lirik menyesuaikan tinggi taskbar horizontal. Saat Anda beralih ke
  ukuran small, widget mengecilkan font agar tetap berada di dalam taskbar,
  bukan berpindah ke atasnya.
- Saat Anda kembali ke taskbar yang lebih tinggi, widget memulihkan ukuran font
  sesuai ruang yang tersedia. Preferensi font di Settings tetap sama.
- Widget tetap memberi jarak dari system tray dan NetSpeedTray. Perilaku untuk
  taskbar vertikal dan garis tipis auto-hide tetap memakai posisi di sebelahnya.

## Pemberitahuan pembaruan

- GlanceLyric memeriksa GitHub setelah widget dibuka dan membatasi pemeriksaan sukses
  menjadi sekali sehari. Gangguan koneksi tidak menghentikan lirik; aplikasi
  mencoba lagi pada startup berikutnya atau pemeriksaan per jam.
- Saat ada versi baru, Anda akan melihat nomor versi dan catatan perubahannya.
  Pilih **Buka halaman unduhan** untuk menuju release resmi, atau **Nanti**.
  Aplikasi tidak mengunduh atau menjalankan installer tanpa tindakan Anda.
- Menu klik kanan **Check for updates…** menyediakan pemeriksaan manual.
  Anda dapat mematikan pemeriksaan otomatis melalui Settings.
- Build uji awal menerima notifikasi pre-release publik dengan label versi uji.
  Aplikasi menampilkan satu pemberitahuan otomatis per versi; pemeriksaan manual
  dapat membuka catatannya kembali.
- Saat Anda membuka rincian catatan yang panjang, dialog menyesuaikan posisinya
  agar bagian bawahnya tidak keluar layar.
- Jika autostart aktif, watcher menunggu Spotify sebelum membuka widget. Popup
  update tidak muncul hanya karena Windows baru login saat widget belum terbuka.
  Tidak ada pemberitahuan jika versi terpasang sudah yang terbaru.

## Untuk pengguna v1.0

v1.0 belum mempunyai pemeriksa update dan tidak bisa menerima popup pembaruan
dari jarak jauh. Unduh dan pasang v1.1.0 secara manual sekali. Mulai v1.1.0,
aplikasi dapat memberi tahu Anda tentang
rilis berikutnya. Installer tetap memakai AppId yang sama dan menyimpan
pengaturan/cache pada `%USERPROFILE%\.glancelyric`.

- Installer: `GlanceLyric-Setup-1.1.0-x64.exe`. Tutup widget dan watcher lama,
  lalu jalankan installer baru. AppId tetap sama agar mengenali instalasi lama.
- Portable: ekstrak `GlanceLyric-v1.1.0-windows-x64.zip` ke folder terpisah.
  Jalankan `GlanceLyric.exe` dan pertahankan `_internal` di sampingnya.
- Cocokkan paket dengan `SHA256SUMS.txt`. Executable masih unsigned dan dapat
  memicu peringatan SmartScreen atau unknown publisher.

Download dan penggunaan tetap gratis. Donasi bukan syarat update.

## Status pengujian

- 432 kombinasi layout native Qt dengan pengukuran taskbar simulasi lulus pada
  skala aplikasi 100/125/150%, termasuk font 7/9/20, taskbar atas/bawah, dan
  NetSpeedTray/TrafficMonitor. Preferensi font tetap sama.
- Pemeriksaan runtime executable, posisi pada taskbar Windows nyata, request
  GitHub otomatis, dialog catatan panjang, dan kegagalan koneksi lulus.
- Pemilik mengonfirmasi uji langsung Spotify dan pergantian mode taskbar pada
  perangkatnya. Ini bukan klaim semua konfigurasi Windows sudah tervalidasi.
- Pengujian manual instalasi/upgrade/uninstall, autostart saat login, perubahan
  DPI OS, Windows 10, dan komputer lain belum selesai. Karena itu rilis ini
  tetap berstatus pre-release.
