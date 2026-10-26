source /usr/share/cachyos-fish-config/cachyos-config.fish

# overwrite greeting
# potentially disabling fastfetch
#function fish_greeting
#    # smth smth
#end
fnm env --use-on-cd | source

# Configuração do Android SDK para o Fish Shell
set -gx ANDROID_HOME $HOME/Android/Sdk
fish_add_path -g -p $ANDROID_HOME/emulator
fish_add_path -g -p $ANDROID_HOME/platform-tools

# Fix Kitty SSH terminfo
if test "$TERM" = "xterm-kitty"
    alias ssh="kitten ssh"
end
