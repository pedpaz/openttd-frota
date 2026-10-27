#!/bin/sh
# Renderiza todos os objetos de cenario.json em sprites-cenario/<modelo>/ (ou só os modelos passados).
cd "$(dirname "$0")/.."
for m in ${@:-$(python3 -c "import json;print(' '.join(json.load(open('cenario.json'))['modelos']))")}; do
  spec=$(python3 -c "import json,sys;print(json.dumps(json.load(open('cenario.json'))['modelos'][sys.argv[1]]))" $m)
  python3 ferramentas/renderizar_objeto.py -- glb/$m.glb sprites-cenario/$m "$spec" > /dev/null 2>&1 && echo "ok $m" || echo "FALHOU $m"
done
