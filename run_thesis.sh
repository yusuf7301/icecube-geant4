#!/bin/bash
# Tüm tez koşularını sırayla çalıştırır (build/ dizininde). Tahmini süre: ~2.5-3 saat (12 thread).
# Kullanım: bash run_thesis.sh [thread_sayısı]
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
THREADS=${1:-12}
bash "$ROOT/macros/make_macros.sh" > /dev/null
cd "$ROOT/build"
mkdir -p logs
for m in param_spacing4m param_spacing8m param_mie \
         scan_0.1TeV scan_0.3TeV scan_1TeV scan_3TeV scan_10TeV scan_30TeV scan_100TeV \
         detail_0.1TeV detail_0.3TeV detail_1TeV detail_3TeV detail_10TeV detail_30TeV detail_100TeV; do
  prefix=$(awk '/^\/icecube\/prefix/{print $2}' "$ROOT/macros/$m.mac")
  if [ -f "${prefix}_events.csv" ]; then echo "$m zaten tamamlanmış, atlanıyor"; continue; fi
  echo "[$(date +%H:%M:%S)] $m başladı"
  /usr/bin/time -f "$m: %e s" -a -o logs/times.txt ./sim "$ROOT/macros/$m.mac" "$THREADS" > "logs/$m.log" 2>&1
  echo "[$(date +%H:%M:%S)] $m bitti"
done
