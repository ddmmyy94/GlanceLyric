# Runtime pihak ketiga

GlanceLyric memakai library berikut; lisensinya terpisah dari lisensi aplikasi:

- Python: PSF License — https://docs.python.org/3/license.html
- PySide6 / Shiboken6 / Qt: distribusi open-source LGPLv3/GPLv3, atau lisensi
  komersial dari Qt. Paket ini memakai jalur open-source dan dynamic library.
  https://doc.qt.io/qtforpython-6/licenses.html
  https://www.qt.io/licensing/open-source-lgpl-obligations
- Requests: Apache-2.0 — https://github.com/psf/requests
- urllib3: MIT — https://github.com/urllib3/urllib3
- charset-normalizer: MIT — https://github.com/jawah/charset_normalizer
- idna: BSD-3-Clause — https://github.com/kjd/idna
- certifi: MPL-2.0 — https://github.com/certifi/python-certifi
- PyWinRT: MIT — https://github.com/pywinrt/pywinrt
- PyInstaller bootloader: GPL dengan exception untuk executable yang dihasilkan.
  https://pyinstaller.org/en/stable/license.html

Build menyertakan teks lisensi yang tersedia dari paket terpasang dalam
`licenses/`, serta teks LGPLv3/GPLv3 dari repository Qt sesuai versi PySide6
dan MIT dari repository PyWinRT. Build membutuhkan internet untuk mengambilnya.
Runtime Qt disimpan sebagai DLL terpisah dalam `_internal/`, bukan
ditautkan statis. Sumber GlanceLyric dan instruksi build ada dalam proyek ini.
Sumber Qt/PySide6 tersedia melalui https://download.qt.io/ dan
https://code.qt.io/pyside/pyside-setup.git/.

Anda boleh mengganti library Qt/PySide6 dengan versi modifikasi yang kompatibel
dan melakukan reverse engineering untuk men-debug modifikasi tersebut sesuai
ketentuan LGPL. Simpan struktur DLL pada `_internal/`; gunakan source proyek dan
`Build.bat` untuk membangun ulang aplikasi bila diperlukan.
