#!/bin/sh
# Para só o jogo do display :99 (usado nos previews) e, se pedido, inicia de novo.
# Uso: teste/meu_jogo.sh parar | teste/meu_jogo.sh iniciar ANO [conjunto_grafico]
for p in $(pgrep -x openttd); do
  tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null | grep -q -- '-r 1600x960' && kill -9 $p
done
[ "$1" = "iniciar" ] || exit 0
pgrep -x Xvfb >/dev/null || (setsid Xvfb :99 -screen 0 1600x960x24 >/dev/null 2>&1 &)
sleep 2
ANO=${2:-1950}; GFX=${3:-OpenGFX2 High Def}
cd ${BIN_DIR:-/home/claude/openttd-motor/build} && DISPLAY=:99 SDL_AUDIODRIVER=dummy setsid ./openttd -I "$GFX" -g -G 4242 -t $ANO -v sdl -s null -m null -b 32bpp-anim -r 1600x960 -d script=4,misc=3 > /tmp/claude-0/-home-claude/57c43f7d-e9ab-5cae-a678-a344d77c3b97/scratchpad/jogo.log 2>&1 &
