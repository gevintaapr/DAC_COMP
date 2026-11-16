# Batas wilayah 38 provinsi (GeoJSON)

- **File**: `indonesia_38_provinsi.geojson` (38 fitur, WGS84 / EPSG:4326)
- **Sumber**: [ardian28/GeoJson-Indonesia-38-Provinsi](https://github.com/ardian28/GeoJson-Indonesia-38-Provinsi)
  (commit `486e89c`, 2024-10-30). Data SHP aslinya dari Badan Informasi Geospasial (geoservice.big.go.id).
- **Lisensi**: MIT, lihat `LICENSE_geojson_ardian28.txt`. Cantumkan atribusi di dashboard:
  "Batas wilayah: BIG via ardian28/GeoJson-Indonesia-38-Provinsi (MIT)".

## Perubahan dari file sumber
Geometri tidak diubah. Properti diganti agar bisa langsung di-join ke dataset proyek:

| Properti | Isi |
|---|---|
| `kode_provinsi` | Kode BPS (kunci join ke `master_long.csv` / `master_wide_2025.csv`) |
| `provinsi`, `iso_3166_2`, `pulau`, `kelompok_wilayah` | Dari `config/provinsi.csv` |
| `kode_prov_sumber`, `nama_sumber` | Nilai asli file sumber |

**Catatan:** kode di file sumber masih kode lama. Papua Barat Daya dan Papua Barat sama-sama `92`, sedangkan
Papua, Papua Selatan, Papua Tengah, dan Papua Pegunungan sama-sama `91`. Karena itu join dilakukan lewat nama,
lalu kode diganti dengan kode BPS.

## Di Tableau
Connect → Spatial file → pilih `indonesia_38_provinsi.geojson`, lalu relasikan `kode_provinsi` dengan
`kode_provinsi` pada `master_wide_2025.csv` atau `master_long.csv`.
