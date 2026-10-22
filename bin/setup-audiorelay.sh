#!/usr/bin/env bash
# Script Universal para AudioRelay no Linux / PipeWire
# Detecta a placa de som padrão automaticamente em qualquer máquina

echo "Configurando espelhamento de áudio para AudioRelay..."

DEF_SINK=$(pactl get-default-sink 2>/dev/null || true)
DEF_SOURCE=$(pactl get-default-source 2>/dev/null || true)

# 1. Cria o sink estéreo que o AudioRelay consegue ler sem erro de canal
if ! pactl list short sinks | grep -q "audiorelay_speaker"; then
    pactl load-module module-null-sink sink_name=audiorelay_speaker sink_properties=device.description=AudioRelay-Speaker
fi

# 2. Espelha TUDO o que toca na saída padrão atual para o AudioRelay-Speaker
if [ -n "$DEF_SINK" ]; then
    if ! pactl list short modules | grep -q "sink=audiorelay_speaker"; then
        pactl load-module module-loopback source="${DEF_SINK}.monitor" sink=audiorelay_speaker sink_dont_move=true source_dont_move=true 2>/dev/null || true
    fi
fi

# 3. Dispositivo de microfone virtual para receber a voz do celular
if ! pactl list short sinks | grep -q "virtual_mic"; then
    pactl load-module module-null-sink sink_name=virtual_mic sink_properties=device.description="Microfone-Virtual-Discord" 2>/dev/null || true
fi

if ! pactl list short sources | grep -q "celular_mic"; then
    pactl load-module module-remap-source master=virtual_mic.monitor source_name=celular_mic source_properties=device.description="Microfone-do-Celular" 2>/dev/null || true
fi

# 4. Mantém dispositivos físicos originais como padrão
[ -n "$DEF_SINK" ] && pactl set-default-sink "$DEF_SINK" 2>/dev/null || true
[ -n "$DEF_SOURCE" ] && pactl set-default-source "$DEF_SOURCE" 2>/dev/null || true

echo "Pronto! Áudio espelhado e dispositivos mantidos como padrão."
