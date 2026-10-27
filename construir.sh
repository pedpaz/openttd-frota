#!/bin/sh
# Gera build/frota.grf a partir dos renders em sprites/. Requer: python3, Pillow, nml (pip install nml).
set -e
cd "$(dirname "$0")"
python3 ferramentas/montar.py
cd build
nmlc -c --grf frota.grf frota.nml
echo "pronto: build/frota.grf"
