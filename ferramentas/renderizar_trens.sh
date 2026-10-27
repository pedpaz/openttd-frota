#!/bin/sh
# Renderiza todos os trens de 1950 (modelos em glb/) em sprites-trens/<slug>/p<parte>/.
cd "$(dirname "$0")/.."
r() { python3 ferramentas/renderizar_trem.py -- glb/$1.glb sprites-trens/$1 $2 > /dev/null 2>&1 && echo "ok $1" || echo "FALHOU $1"; }
[ -n "$1" ] && { r "$1" "$2"; exit; }
r kirby_paul_tank 8,4
r chaney_jubilee 8,8,8,2
r ginzu_a4 8,8,8,4
r sh_8p 8,8,8,4
for w in passenger_carriage mail_van coal_truck oil_tanker livestock_van goods_van grain_hopper wood_truck iron_ore_hopper steel_truck armoured_van; do r $w 8; done
