# openttd-frota

Mod de veículos (NewGRF) para o OpenTTD / JGR Patchpack. Os veículos originais do TTD, com os **nomes originais**, ganham gráficos renderizados a partir de modelos 3D fiéis aos protótipos reais, em zoom 4× e 32 bits. As regras do jogo (preço, velocidade, capacidade) continuam as mesmas.

Faz par com o motor do jogo em [pedpaz/openttd-motor](https://github.com/pedpaz/openttd-motor).

## Como funciona

1. `modelos/modelar.py` gera os modelos 3D (Blender, `bpy`) em `glb/`.
2. `ferramentas/renderizar.py` transforma cada modelo nas 8 direções do jogo, na projeção do OpenTTD, e salva em `sprites/<veículo>/`.
3. `construir.sh` monta as folhas de sprites (1×, 2× e 4×, mais a base 8 bits na paleta do TTD) e compila `build/frota.grf` com o NML.

O GitHub roda o passo 3 sozinho a cada envio e deixa o `frota.grf` para baixar na aba **Actions**.

## Veículos

| Veículo | Modelo 3D | No jogo |
|---|---|---|
| MPS Regal Bus | ✔ | ✔ |
| Balogh Coal Truck | ✔ | ✔ |
| MPS Mail Truck | ✔ | ✔ |
| Witcombe Oil Tanker | ✔ | ✔ |
| Talbott Livestock Van | ✔ | ✔ |
| Balogh Goods Truck | ✔ | ✔ |
| Hereford Grain Truck | ✔ | ✔ |
| Witcombe Wood Truck | ✔ | ✔ |
| MPS Iron Ore Truck | ✔ | ✔ |
| Balogh Steel Truck | ✔ | ✔ |
| Balogh Armoured Truck | ✔ | ✔ |

## Comandos

```sh
# gerar os modelos
python3 modelos/modelar.py -- glb
# renderizar um veículo
python3 ferramentas/renderizar.py -- glb/mps_regal_bus.glb sprites/mps_regal_bus
# compilar o mod
./construir.sh
```

Licença: GPL v2, como o OpenTTD.

## Trens de 1950 (tamanho real)

| Trem | Tipo real | Comprimento | Partes no jogo |
|---|---|---|---|
| Kirby Paul Tank | GWR 5700 (0-6-0 tanque) | 9,0 m | 8 + 4 |
| Chaney 'Jubilee' | LMS Jubilee + tênder Fowler | 19,5 m | 8 + 8 + 8 + 2 |
| Ginzu 'A4' | LNER A4 + tênder de corredor | 21,0 m | 8 + 8 + 8 + 4 |
| SH '8P' | BR Standard 8P 71000 + tênder BR1J | 21,0 m | 8 + 8 + 8 + 4 |
| 11 vagões | tipos britânicos de 4 rodas | 6,0 m | 8 |

Escala: 1 tile = 12 m, então 8 unidades de comprimento (meio tile) = 6 m. As locomotivas com tênder ocupam o espaço
de 3 a 3,5 vagões, como na vida real. As partes extras (ids 200+) são articuladas, não têm peso, potência, custo nem
carga: potência, peso, velocidade, preço e capacidade continuam os do jogo original.

Modelos em `modelos/trens.py`; render dividido em partes por `ferramentas/renderizar_trem.py` (corta o modelo no
shader e centraliza cada parte) ou `ferramentas/renderizar_trens.sh` para todos.

## Física

Os 11 rodoviários usam o peso vazio de caminhões e ônibus britânicos da época (4,2 a 6,8 t), a potência original,
coeficiente de tração de pneu (0,42 a 0,45) e arrasto pelo formato da carroceria (tanque e caçamba menos, baú e
ônibus mais). Valores na tabela `FISICA` do `ferramentas/montar.py`. A carga continua pesando conforme o tipo de carga.

## Cenário (cenario.grf)

Um segundo mod, `cenario.grf`, troca sprites do cenário que o OpenGFX2 High Def ainda não tem em 4×, sem mudar regra
nenhuma: estátua equestre, chafariz, as duas praças e o estádio (com o gramado) das cidades, e todas as peças da mina
de carvão e da usina termelétrica. Os modelos ficam em `modelos/cidade.py` e `modelos/industria.py`; a lista de
sprites trocados, com a posição de referência de cada um no tile, fica em `cenario.json`. Para renderizar:
`ferramentas/renderizar_cenario.sh` (ou só alguns modelos). O alinhamento é o mesmo do jogo: cada sprite é desenhado
a partir do ponto do subtile definido no código do OpenTTD.

## Cor da empresa

A pintura de cada veículo sai do render em cinza e ganha uma **máscara**: o jogo troca esse cinza pela cor de cada companhia e só aproveita o sombreado do render. Os materiais tratados como pintura estão em `NOMES_PINTURA`, no `ferramentas/renderizar.py`.

## Teste

`teste/ai/Vitrine` é uma IA usada só nos previews: ela pega a maior cidade, monta pontos de ônibus e de caminhão e põe linhas para rodar.
