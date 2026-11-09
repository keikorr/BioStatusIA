#!/usr/bin/env bash
# Reproduces every audit output cited in the revised manuscript.
# Usage: bash run_all.sh   (needs git, Python >= 3.10, requirements-audit.txt)
set -euo pipefail
cd "$(dirname "$0")"
WORK=${WORK:-_sources}
mkdir -p "$WORK"
if [ ! -d "$WORK/mm" ]; then
  git clone https://github.com/JuniorSoares716/BioStatusIA_MultiModal "$WORK/mm"
fi
git -C "$WORK/mm" checkout -q 2d89637b752e12460954f1d449586e8ec88cf469
if [ ! -d "$WORK/bs" ]; then
  git clone -b atualizacao_features https://github.com/keikorr/BioStatusIA "$WORK/bs"
fi
git -C "$WORK/bs" checkout -q 6960fd60c426e0b2728e0226311ae99399e14c31
echo "699cb605748a963b3897786058ccb25a21b09bb13f7e09795c5bb102b4884c48  $WORK/bs/reports/benchmark_artigo2/resultados.json" | sha256sum -c -
python3 -I scripts/01_verify_published_metrics.py
python3 -I scripts/02_code_protocol_checklist.py --audited "$WORK/mm" --lineage "$WORK/bs"
python3 -I scripts/03_calibration_oof.py --results "$WORK/bs/reports/benchmark_artigo2/resultados.json"
echo "Outputs in ./outputs and ./figures"
