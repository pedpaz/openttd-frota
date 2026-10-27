#!/bin/sh
# Gera build/frota.grf a partir dos renders em sprites/. Requer: python3, Pillow, nml (pip install nml).
set -e
cd "$(dirname "$0")"
python3 ferramentas/montar.py
python3 ferramentas/montar_cenario.py
cd build
nmlc -c --grf frota.grf frota.nml
nmlc -c --grf cenario.grf cenario.nml
echo "pronto: build/frota.grf e build/cenario.grf"
