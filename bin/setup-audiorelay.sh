#!/usr/bin/env bash
# Script não-invasivo para AudioRelay no Linux / PipeWire
# Mantém seus dispositivos físicos como padrão e apenas espelha o áudio

echo "Configurando espelhamento de áudio para AudioRelay..."

# 1. Cria o sink estéreo que o AudioRelay consegue ler sem erro de canal
if ! pactl list short sinks | grep -q "audiorelay_speaker"; then
    pactl load-module module-null-sink sink_name=audiorelay_speaker sink_properties=device.description=AudioRelay-Speaker
fi

# 2. Espelha TUDO o que toca na sua saída padrão (Top Use USB) para o AudioRelay-Speaker
if ! pactl list short modules | grep -q "sink=audiorelay_speaker"; then
    pactl load-module module-loopback source=alsa_output.usb-Top_Use_Top_Use_USB-00.analog-stereo.monitor sink=audiorelay_speaker sink_dont_move=true source_dont_move=true
fi

# 3. Dispositivo de microfone virtual para receber a voz do celular
if ! pactl list short sinks | grep -q "virtual_mic"; then
    pactl load-module module-null-sink sink_name=virtual_mic sink_properties=device.description="Microfone-Virtual-Discord"
fi

if ! pactl list short sources | grep -q "celular_mic"; then
    pactl load-module module-remap-source master=virtual_mic.monitor source_name=celular_mic source_properties=device.description="Microfone-do-Celular" 2>/dev/null
fi

# 4. Garante que seus dispositivos físicos continuam como os padrões do Linux
pactl set-default-sink alsa_output.usb-Top_Use_Top_Use_USB-00.analog-stereo
pactl set-default-source alsa_input.usb-Top_Use_Top_Use_USB-00.mono-fallback

echo "Pronto! Áudio espelhado e dispositivos físicos mantidos como padrão."
