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

## Cor da empresa

A pintura de cada veículo sai do render em cinza e ganha uma **máscara**: o jogo troca esse cinza pela cor de cada companhia e só aproveita o sombreado do render. Os materiais tratados como pintura estão em `NOMES_PINTURA`, no `ferramentas/renderizar.py`.

## Teste

`teste/ai/Vitrine` é uma IA usada só nos previews: ela pega a maior cidade, monta pontos de ônibus e de caminhão e põe linhas para rodar.
