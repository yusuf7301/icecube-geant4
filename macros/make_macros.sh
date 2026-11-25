#!/bin/bash
# Tez çalışması için tüm makroları üretir: enerji taraması + parametre çalışması.
# Kullanım: bash macros/make_macros.sh   (proje kök dizininden)
cd "$(dirname "$0")"

write_macro () {   # $1=dosya $2=enerji(TeV) $3=olay $4=prefix $5=buz modeli $6=string aralığı(m) [$7=1: ayrıntılı kayıt]
  local off="OpMieHG"; [ "$5" == "mie" ] && off="OpRayleigh"
  local det=${7:-0}
  cat > "$1" <<MAC
# Otomatik üretildi (make_macros.sh): E = $2 TeV, $3 olay, buz = $5, string aralığı = $6 m
/control/verbose 1
/run/printProgress 20
/icecube/stringSpacing $6 m
/run/initialize
/process/inactivate $off
/icecube/particle mu-
/icecube/energy $2 TeV
/icecube/sourceRA 77.358 deg
/icecube/sourceDec 5.693 deg
/icecube/angularSpread 0.5 deg
/icecube/offsetRadius 3 m
/icecube/prefix $4
/icecube/photonSaveEvents $det
/icecube/saveHitPhotons $det
/icecube/saveMuonSteps $det
/run/beamOn $3
MAC
}

# 1) Enerji taraması (Rayleigh buz, 6 m aralık)
for spec in 0.1:300 0.3:300 1:300 3:200 10:200 30:100 100:20; do
  E=${spec%%:*}; N=${spec##*:}
  write_macro "scan_${E}TeV.mac" "$E" "$N" "data/scan/E${E}TeV" rayleigh 6
done

# 2) Parametre çalışması (1 TeV): string aralığı ve buz modeli
for S in 4 8; do
  write_macro "param_spacing${S}m.mac" 1 300 "data/param/spacing${S}m" rayleigh "$S"
done
write_macro "param_mie.mac" 1 300 "data/param/mie" mie 6

# 3) Ayrıntılı koşular (foton, hit ve müon adımı kaydı açık): fizik ve AGN figürlerinin 1–4. panelleri için.
#    Yüksek enerjide süre ve dosya boyutu hızla arttığı için olay sayısı azaltılır.
for spec in 0.1:100 0.3:100 1:100 3:100 10:50 30:30 100:10; do
  E=${spec%%:*}; N=${spec##*:}
  write_macro "detail_${E}TeV.mac" "$E" "$N" "data/detail/E${E}TeV" rayleigh 6 1
done
ls
