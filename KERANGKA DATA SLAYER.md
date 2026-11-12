**DOKUMEN KONSEP DAN IMPLEMENTASI DASHBOARD**

**Pendidikan dan Pembangunan Sumber Daya Manusia di Indonesia**

*Bahan diskusi internal tim  \|  Disusun: 10 November 2026  \|  Status: draf*

# **1\. Tujuan Dokumen**

Dokumen ini memuat gagasan analisis serta cara pelaksanaannya, mulai dari rumusan masalah, kerangka variabel, rancangan dashboard dua halaman, metode analisis, hingga langkah kerja dan pembagian peran. Dokumen disusun sebagai bahan diskusi sehingga seluruh isinya terbuka untuk diubah sesuai kesepakatan tim. Bagian 10 memuat daftar hal yang perlu diputuskan bersama.

# **2\. Gagasan Utama**

## ***2.1 Latar Belakang Singkat***

Pendidikan lazim dipandang sebagai fondasi pembangunan sumber daya manusia (SDM). Namun capaian pendidikan tidak selalu sejalan dengan kualitas SDM dan kondisi ketenagakerjaan. Sebagian daerah memiliki lama sekolah yang tinggi tetapi pengangguran terbuka juga tinggi, sedangkan daerah lain menunjukkan pola sebaliknya. Dashboard ini dirancang untuk memperlihatkan di mana kesenjangan itu terjadi dan seberapa kuat keterkaitan antara pendidikan dan kualitas SDM.

## ***2.2 Judul Kerja (usulan)***

“Dari Bangku Sekolah ke Dunia Kerja: Apakah Capaian Pendidikan Berkaitan dengan Kualitas Sumber Daya Manusia di Indonesia?”

## ***2.3 Pertanyaan Utama***

Apakah daerah dengan capaian pendidikan yang lebih baik juga memiliki kualitas SDM dan kondisi ketenagakerjaan yang lebih baik, serta di mana letak kesenjangan antardaerah?

## ***2.4 Pertanyaan Turunan***

1. Bagaimana gambaran dan kesenjangan capaian pendidikan antarprovinsi (misalnya RLS, HLS, APS)?

2. Apakah RLS yang lebih tinggi berhubungan dengan persentase pekerja formal yang lebih tinggi dan pengangguran yang lebih rendah?

3. Apakah akses internet (sebagai proxy penguasaan teknologi) berhubungan dengan persentase pemuda NEET yang lebih rendah?

4. Provinsi mana yang menunjukkan pola tidak biasa, misalnya pendidikan tinggi tetapi pengangguran juga tinggi?

5. Provinsi dapat dikelompokkan ke dalam berapa kelompok berdasarkan profil pendidikan dan SDM, dan rekomendasi apa yang cocok untuk tiap kelompok?

## ***2.5 Hipotesis Kerja***

Hipotesis berikut bersifat dugaan awal yang akan diuji dengan data, bukan kesimpulan.

* Provinsi dengan RLS lebih tinggi cenderung memiliki persentase pekerja formal lebih tinggi.

* Provinsi dengan akses internet lebih luas cenderung memiliki persentase NEET lebih rendah.

* Pendidikan tinggi tidak otomatis berarti pengangguran rendah; pada sebagian provinsi lulusan jenjang tertentu (misalnya SMK atau universitas) justru menghadapi TPT yang tinggi.

* Provinsi dapat dikelompokkan menjadi beberapa profil yang berbeda sehingga rekomendasi tidak dapat disamaratakan.

# **3\. Kerangka Konsep: Input – Output – Outcome**

Variabel disusun dalam tiga lapisan agar alur cerita runtut dan tidak ada variabel yang tumpang tindih. Alurnya: pendidikan yang diterima (input) membentuk kualitas SDM (output) yang tercermin pada hasil di pasar kerja dan kesejahteraan (outcome).

| Lapisan | Makna | Contoh indikator |
| ----- | ----- | ----- |
| Input pendidikan | Seberapa besar akses dan durasi pendidikan yang diterima penduduk. | Rata-rata Lama Sekolah (RLS), Harapan Lama Sekolah (HLS), Angka Partisipasi Sekolah (APS). |
| Output SDM | Kemampuan dan kualitas SDM yang terbentuk. | Indeks Pembangunan Manusia (IPM), akses internet dan penguasaan teknologi. |
| Outcome ekonomi | Hasil nyata di pasar kerja dan kesejahteraan. | Tingkat Pengangguran Terbuka (TPT) menurut pendidikan, pekerja formal vs informal, NEET, kemiskinan. |

# **4\. Variabel dan Sumber Data**

## ***4.1 Daftar Variabel***

Data bersumber dari Badan Pusat Statistik (BPS). Seluruh variabel perlu diverifikasi ketersediaannya (per provinsi dan per tahun) sebelum ditetapkan. Variabel “inti” menjadi dasar dashboard; variabel “opsional” dipakai bila datanya lengkap dan waktu mencukupi. Target variabel inti adalah 8 sampai 12 agar analisis tetap dalam dan tidak dangkal.

| Lapisan | Variabel | Kemungkinan sumber di BPS | Prioritas |
| ----- | ----- | ----- | ----- |
| Input | Rata-rata Lama Sekolah (RLS) | Indikator pendidikan / komponen IPM | Inti |
| Input | Harapan Lama Sekolah (HLS) | Indikator pendidikan / komponen IPM | Inti |
| Input | Angka Partisipasi Sekolah (APS) usia 16–18 dan 19–23 tahun | Statistik pendidikan (Susenas) | Inti |
| Input | Persentase penduduk berpendidikan tinggi (Diploma ke atas) | Susenas / Sakernas | Opsional |
| Output | Indeks Pembangunan Manusia (IPM) | Publikasi dan tabel IPM | Inti |
| Outcome | TPT secara umum | Sakernas | Inti |
| Outcome | TPT menurut pendidikan tertinggi (SMA, SMK, Diploma, Universitas) | Sakernas | Inti |
| Outcome | Persentase pekerja formal dan informal | Sakernas | Inti |
| Outcome | Persentase pemuda NEET | Sakernas / Statistik pemuda | Inti |
| Outcome | Persentase penduduk miskin | Susenas | Inti |
| Outcome | Rata-rata upah atau pengeluaran per kapita | Sakernas / Susenas | Opsional |
| Inklusivitas | Perbandingan perkotaan–perdesaan dan laki-laki–perempuan (misalnya RLS) | Tabel BPS menurut klasifikasi daerah dan jenis kelamin | Opsional |

## ***4.2 Variabel dari Rancangan Awal yang Dikeluarkan atau Diubah***

| Variabel awal | Keputusan dan alasan |
| ----- | ----- |
| Kualitas hasil belajar, literasi, dan numerasi (skor) | Dikeluarkan. Skor AKM atau PISA bukan data BPS. Dapat diganti dengan angka melek huruf atau proxy lain dari BPS bila tersedia. |
| Karakter, etos kerja, dan kemampuan sosial (soft skills) | Dikeluarkan. Tidak ada indikator terukur di BPS. |
| Literasi digital (muncul dua kali di rancangan awal) | Digabung menjadi satu kelompok, yaitu akses internet dan penguasaan teknologi, pada lapisan Output SDM. |
| Kesesuaian kompetensi dengan pasar kerja (skills match dan vokasi) | Diubah menjadi analisis TPT menurut jenjang pendidikan (SMA vs SMK vs Diploma vs Universitas) sebagai proxy yang tersedia. |

## ***4.3 Prinsip Pengumpulan Data***

* Level data utama adalah provinsi (38 provinsi). Level kabupaten/kota dapat dipertimbangkan bila datanya tersedia dan waktu memungkinkan.

* Gunakan rentang tahun yang sama untuk seluruh variabel (misalnya beberapa tahun terakhir sesuai ketersediaan) agar perbandingan adil.

* Catat sumber setiap data (judul tabel, tahun rilis, tautan, tanggal unduh) pada Lampiran sejak awal.

* Simpan data mentah apa adanya, lakukan pembersihan pada salinan terpisah, dan dokumentasikan setiap perubahan.

* Periksa konsistensi data provinsi yang mengalami pemekaran (khususnya wilayah Papua) dan beri catatan bila ada data yang tidak lengkap.

# **5\. Rancangan Dashboard (Dua Halaman)**

Dashboard dibagi menjadi dua halaman dengan peran berbeda: halaman 1 menjawab “apa dan di mana” (gambaran dan kesenjangan), halaman 2 menjawab “mengapa dan apa hubungannya” (analisis mendalam). Halaman 1 bukan tempat menampilkan data mentah, melainkan ringkasan yang sudah diolah. Data mentah tetap disimpan pada dataset pendukung.

## ***5.1 Halaman 1: Gambaran dan Kesenjangan (analisis deskriptif)***

| Komponen | Isi |
| ----- | ----- |
| Judul dan filter | Filter tahun, provinsi, dan kelompok wilayah (misalnya Jawa dan luar Jawa). |
| Kartu KPI | RLS nasional, IPM, TPT, persentase NEET, persentase pekerja formal. |
| Peta sebaran provinsi | Peta berwarna (choropleth) dengan pilihan indikator. |
| Peringkat provinsi | Diagram batang provinsi tertinggi dan terendah untuk indikator terpilih. |
| Tren waktu | Diagram garis perkembangan beberapa indikator utama dari tahun ke tahun. |
| Kotak insight | Satu sampai tiga kalimat temuan utama halaman ini. |

## ***5.2 Halaman 2: Hubungan dan Insight (analisis mendalam)***

| Komponen | Isi |
| ----- | ----- |
| Diagram pencar (scatter plot) dengan garis tren | RLS vs TPT; RLS vs persentase pekerja formal; akses internet vs NEET. |
| Matriks korelasi (heatmap) | Korelasi antarvariabel inti beserta penjelasan singkat cara membacanya. |
| Analisis TPT menurut pendidikan | Perbandingan TPT lulusan SMA, SMK, Diploma, dan Universitas per provinsi atau kelompok provinsi (proxy kesesuaian dengan pasar kerja). |
| Pengelompokan provinsi (klaster) | 3 sampai 4 kelompok, misalnya pendidikan tinggi dan SDM kuat; pendidikan tinggi tetapi pengangguran tinggi; pendidikan dan SDM tertinggal. |
| Temuan kunci | 3 sampai 5 temuan utama dalam bahasa yang ringkas. |
| Rekomendasi | Rekomendasi kebijakan atau tindakan berdasarkan temuan, sesuai kelompok provinsi. |

## ***5.3 Alur Cerita (Data Storytelling)***

1. **Kondisi:** bagaimana capaian pendidikan dan SDM saat ini, dan seberapa besar jarak antardaerah (halaman 1).

2. **Hubungan:** apakah pendidikan yang lebih baik berkaitan dengan SDM dan pasar kerja yang lebih baik (halaman 2, scatter dan korelasi).

3. **Kejutan:** daerah mana yang menyimpang dari pola umum dan apa kemungkinan penyebabnya (halaman 2, kasus menyimpang dan TPT menurut pendidikan).

4. **Profil:** kelompok provinsi dengan karakter yang serupa (halaman 2, klaster).

5. **Tindakan:** rekomendasi yang berbeda untuk tiap kelompok (halaman 2, rekomendasi).

## ***5.4 Pemilihan Platform***

| Platform | Pertimbangan umum | Hal yang perlu dicek tim |
| ----- | ----- | ----- |
| Looker Studio | Gratis, berbasis web, mudah membagikan tautan, cocok untuk kerja bersama dari jarak jauh. | Kemampuan analitik terbatas; perhitungan lanjutan (misalnya klaster) sebaiknya dilakukan di luar lalu diimpor. |
| Power BI | Fitur analisis dan pemodelan data kuat, tersedia visual untuk pengelompokan dan hubungan antarvariabel. | Cara membagikan dashboard ke pihak lain; versi yang dipakai anggota tim. |
| Tableau | Visualisasi sangat fleksibel dan peta mudah dibuat. | Ketersediaan lisensi dan cara publikasi. |

Rekomendasi sementara: pilih platform yang paling dikuasai anggota tim, dengan prioritas kemudahan membagikan dashboard kepada pihak lain. Keputusan akhir diambil dalam diskusi.

## ***5.5 Prinsip Desain***

* Satu grafik menjawab satu pertanyaan, disertai judul yang menyatakan pesan (bukan hanya nama variabel).

* Gunakan palet warna terbatas dan konsisten pada seluruh halaman; label dan satuan harus jelas.

* Pilih jenis grafik sesuai tujuan: peta untuk sebaran wilayah, batang untuk peringkat, garis untuk tren, pencar untuk hubungan.

* Hindari halaman yang terlalu padat; sediakan ruang kosong dan hierarki visual yang jelas.

* Cantumkan sumber data dan tahun pada bagian bawah setiap halaman.

# **6\. Metode Analisis**

| Metode | Tujuan | Catatan |
| ----- | ----- | ----- |
| Statistik deskriptif | Menggambarkan rata-rata, sebaran, nilai tertinggi dan terendah. | Dasar untuk halaman 1\. |
| Analisis kesenjangan | Membandingkan provinsi dan kelompok wilayah. | Dapat berupa selisih tertinggi–terendah atau rasio. |
| Korelasi (Pearson atau Spearman) | Mengukur kekuatan hubungan antarvariabel. | Spearman lebih aman bila ada pencilan atau sebaran tidak normal. |
| Regresi sederhana (opsional) | Menggambarkan arah dan besar hubungan dua variabel. | Hanya bila tim memahami interpretasinya. |
| Klasterisasi (K-Means atau hierarki) | Mengelompokkan provinsi dengan profil serupa. | Variabel perlu distandarisasi; jumlah klaster ditentukan dengan alasan yang jelas. |
| Analisis kasus menyimpang (outlier) | Menemukan provinsi dengan pola tidak biasa. | Sumber insight yang kontra-intuitif dan mudah diingat. |

## ***Catatan Metodologis***

* Korelasi tidak sama dengan sebab-akibat. Gunakan ungkapan “berhubungan dengan” atau “berasosiasi dengan”, bukan “menyebabkan”.

* Jumlah provinsi hanya 38 sehingga sampel kecil. Hasil korelasi perlu ditafsirkan hati-hati; data beberapa tahun atau data kabupaten/kota dapat memperkuat analisis.

* Perhitungan lanjutan yang tidak didukung platform (misalnya klaster) dapat dikerjakan di Python, R, atau Excel, kemudian hasilnya diimpor sebagai kolom baru pada dataset.

* Dokumentasikan langkah dan rumus agar hasil dapat dijelaskan dan direproduksi.

# **7\. Langkah Implementasi**

## ***7.1 Tahapan Kerja***

Estimasi durasi bersifat perkiraan dan dapat digeser sesuai waktu yang tersedia; beberapa tahap dapat berjalan paralel antaranggota.

| No | Tahap | Aktivitas | Keluaran (estimasi) |
| ----- | ----- | ----- | ----- |
| 1 | Finalisasi konsep | Menyepakati judul, pertanyaan, variabel inti, platform, dan pembagian peran. | Dokumen keputusan (1 – 2 hari) |
| 2 | Pengumpulan data | Mencari dan mengunduh tabel BPS untuk tiap variabel; mencatat sumber; mengganti variabel yang datanya tidak tersedia. | Dataset mentah dan daftar sumber (3 – 4 hari) |
| 3 | Pembersihan dan penggabungan | Menyeragamkan nama provinsi, tahun, dan satuan; menangani data kosong; menggabungkan seluruh variabel menjadi satu tabel. | Dataset bersih tunggal (2 hari) |
| 4 | Analisis | Statistik deskriptif, korelasi, TPT menurut pendidikan, klaster, dan pencarian kasus menyimpang; mencatat temuan. | Daftar temuan kunci (2 – 3 hari) |
| 5 | Perancangan dan pembuatan dashboard | Membuat sketsa (wireframe) dua halaman, menghubungkan data ke platform, membangun grafik dan filter. | Dashboard versi 1 (3 – 4 hari) |
| 6 | Narasi dan penyempurnaan | Menulis insight dan rekomendasi, merapikan desain, memeriksa angka dan label. | Dashboard versi 2 (1 – 2 hari) |
| 7 | Review dan uji | Review silang antaranggota; uji akses dashboard dari akun lain; uji filter dan interaksi; ekspor PDF. | Dashboard final (1 – 2 hari) |

## ***7.2 Rancangan Struktur Dataset***

Agar mudah dihubungkan ke platform mana pun, gunakan satu tabel utama dalam format panjang (long format) dengan satu baris untuk setiap kombinasi provinsi, tahun, dan indikator.

| Kolom | Contoh isi | Keterangan |
| ----- | ----- | ----- |
| provinsi | Jawa Tengah | Gunakan penulisan seragam di seluruh tabel. |
| kode\_provinsi | 33 | Memudahkan penggabungan dan pembuatan peta. |
| tahun | 2024 | Gunakan rentang tahun yang sama untuk seluruh indikator. |
| indikator | RLS | Nama baku indikator. |
| nilai | 8,05 | Nilai numerik; satuan dicatat pada kolom terpisah. |
| satuan | tahun / persen | Mencegah salah baca satuan. |
| kelompok\_wilayah | Jawa | Kolom bantu untuk filter dan perbandingan. |
| sumber | Nama tabel BPS | Untuk penelusuran dan dokumentasi. |

Untuk analisis korelasi dan klaster, tabel panjang ini diubah menjadi format lebar (satu baris per provinsi per tahun, satu kolom per variabel). Hasil klaster ditambahkan sebagai kolom baru, lalu diimpor kembali ke dashboard.

## ***7.3 Alat Bantu***

* **Pengumpulan dan pembersihan awal:** Excel atau Google Sheets; untuk pembersihan lebih besar dapat memakai Python (pandas) atau R.

* **Analisis lanjutan:** Python atau R untuk korelasi dan klaster; Excel untuk perhitungan sederhana.

* **Pembuatan dashboard:** platform visualisasi yang dipilih tim.

* **Kerja bersama:** satu folder bersama berisi data mentah, data bersih, hasil analisis, dan catatan sumber, dengan penamaan berkas yang seragam.

# **8\. Pembagian Peran Tim**

Dengan tiga anggota, satu orang dapat memegang lebih dari satu peran. Namun seluruh anggota perlu memahami keseluruhan alur analisis agar dapat menjelaskannya dengan baik.

| Peran | Tanggung jawab | Penanggung jawab |
| ----- | ----- | ----- |
| Koordinator dan penyusun narasi | Mengelola jadwal, menyusun alur cerita, insight, dan rekomendasi, serta memeriksa kelengkapan hasil. | ................ |
| Pengelola data | Mencari dan mengunduh data, membersihkan dan menggabungkan data, mendokumentasikan sumber. | ................ |
| Analis | Melakukan analisis korelasi, klaster, dan analisis lanjutan; memastikan ketepatan perhitungan. | ................ |
| Perancang dashboard | Membuat wireframe, membangun dashboard, mengatur desain dan interaksi, mengekspor hasil. | ................ |

# **9\. Risiko dan Mitigasi**

| Risiko | Mitigasi |
| ----- | ----- |
| Data variabel tertentu tidak tersedia atau tahunnya tidak konsisten | Verifikasi ketersediaan sebelum variabel ditetapkan; siapkan variabel cadangan. |
| Data wilayah pemekaran (Papua) tidak lengkap | Gunakan tahun yang konsisten atau beri catatan jelas pada dashboard. |
| Waktu pengerjaan terbatas | Ikuti tahapan kerja, batasi variabel inti 8 sampai 12, sisakan waktu cadangan di akhir. |
| Dashboard tidak dapat dibuka pihak lain | Uji tautan atau berkas dari akun lain sebelum dibagikan. |
| Klaim sebab-akibat yang berlebihan | Gunakan bahasa asosiasi dan cantumkan keterbatasan analisis. |
| Dashboard terlalu padat | Satu grafik satu pertanyaan; hapus grafik yang tidak mendukung pesan utama. |
| Perhitungan lanjutan tidak didukung platform | Hitung di alat lain lalu impor hasilnya; dokumentasikan langkahnya. |
| Hasil analisis tidak sesuai hipotesis | Tetap dilaporkan apa adanya; temuan yang berbeda dari dugaan sering menjadi insight yang menarik. |

# **10\. Hal yang Perlu Diputuskan dalam Diskusi**

1. Platform yang digunakan dan siapa anggota yang paling menguasainya.

2. Judul kerja dan pertanyaan utama final.

3. Daftar variabel inti final dan variabel opsional yang akan dimasukkan.

4. Level data (hanya provinsi, atau ditambah kabupaten/kota) dan rentang tahun yang dipakai.

5. Pembagian peran dan penanggung jawab setiap tahap.

6. Metode analisis yang akan dipakai dan alat bantu di luar platform (Python, R, atau Excel).

7. Jumlah klaster yang diharapkan dan cara menentukannya.

# **Lampiran. Catatan Sumber Data BPS (untuk diisi tim)**

| Variabel | Judul tabel BPS | Tahun | Level | Tautan | Catatan |
| ----- | ----- | ----- | ----- | ----- | ----- |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

