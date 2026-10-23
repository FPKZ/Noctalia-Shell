# 🌌 CachyOS: Hyprland + Noctalia Shell (Setup Portátil & Universal)

Setup completo, estável e portátil para **CachyOS / Arch Linux**, unindo o poder do compositor **Hyprland** com a elegância do **Noctalia Shell**, projetado para coexistir perfeitamente lado a lado com o **KDE Plasma** sem nenhum conflito de pacotes ou configurações.

---

## ✨ Recursos e Ajustes Incluídos

- ⌨️ **Teclado PT-BR ABNT2 Nativo:** Configurado diretamente em `inputs.lua` e sincronizado com o compositor.
- 📜 **Cheatsheet Interativo de Teclas:** Pressione `Super + F1` ou `Super + /` para abrir um menu pesquisável com todos os atalhos do sistema.
- 💾 **Restauração de Sessão Automática:** Script em segundo plano (`session.py`) que salva periodicamente as janelas e seus respectivos workspaces, restaurando-os silenciosamente após reiniciar o PC.
- 🎨 **Consistência Visual do Dolphin / Apps KDE:** Integração via `qt6ct` e `noctalia.colors`. O Dolphin abre no modo escuro perfeito sem conflitar ou poluir a sessão do KDE Plasma.
- 🖼️ **Wallpaper e Tema Material You:** O wallpaper personalizado é transferido e o Noctalia gera a paleta harmônica (M3 tonal spot + Oxocarbon) com dock e barra flutuante pré-configurados.
- ⚡ **Eliminação de Piscadas no Boot (Early KMS):** O script instalador detecta automaticamente se a sua GPU é **AMD (`amdgpu`)**, **NVIDIA (`nvidia`)** ou **Intel (`i915`)** e injeta o módulo correto no `mkinitcpio.conf`.
- 🔊 **AudioRelay Universal:** Script dinâmico em PipeWire (`setup-audiorelay.sh`) que detecta a placa de som padrão de qualquer PC e cria o canal de espelhamento e microfone virtual sem alterar seus dispositivos físicos.
- 📱 **KDE Connect Integrado:** Serviço de usuário em segundo plano gerenciado pelo systemd com regras de firewall abertas por padrão.
- 💻 **Terminal Kitty & Fish:** Configurado com `xterm-256color` e alias `ssh = kitten ssh` para conexões remotas sem quebra do comando `clear`.
- 🖥️ **Detecção Automática de Monitores:** Detecta os monitores primários e secundários reais do hardware na instalação, adaptando resoluções e workspaces para laptops ou desktops.
- 🛡️ **Coexistência 100% Segura com KDE Plasma:** Não substitui lançadores do sistema, não mexe no KWin/Plasma e reconstrói o cache de aplicativos (`kbuildsycoca6`) para garantir que os atalhos da barra de tarefas do KDE funcionem perfeitamente.

---

## 🚀 Como Instalar

Você pode instalar de duas maneiras:

### Opção 1: Clonando o Repositório (Recomendado)

```bash
git clone https://github.com/SEU-USUARIO/cachyos-hypr-noctalia.git
cd cachyos-hypr-noctalia
chmod +x install.sh
./install.sh
```

### Opção 2: Baixando o Pacote Compactado (.tar.gz) da Release

Baixe o arquivo `noctalia-cachyos-portable.tar.gz` na aba [Releases](releases) e execute:

```bash
tar -xzf noctalia-cachyos-portable.tar.gz
cd cachyos-hypr-noctalia
./install.sh
```

Ao término da instalação, encerre a sessão ou reinicie o computador e selecione **Hyprland (UWSM)** na tela de login (SDDM).

---

## ⌨️ Atalhos Principais

| Atalho | Ação |
| :--- | :--- |
| `Super + Return` | Abre o terminal **Kitty** |
| `Super + E` | Abre o gerenciador de arquivos **Dolphin** |
| `Super + D` | Abre o lançador de aplicativos (Noctalia launcher) |
| `Super + Q` | Fecha a janela ativa |
| `Super + F1` ou `Super + /` | **Cheatsheet:** Exibe todos os atalhos do sistema |
| `Super + F` | Alterna modo tela cheia |
| `Super + Espaço` | Alterna modo janela flutuante |
| `Super + 1..9` | Alterna para o workspace 1 ao 9 |
| `Super + Shift + 1..9` | Move a janela focada para o workspace 1 ao 9 |

---

## 🔄 Como Atualizar o Repositório com as Configurações do seu PC

Para capturar qualquer nova alteração feita no seu sistema atual (atalhos, dock, cores, novos scripts ou wallpaper) e atualizar este repositório automaticamente:

```bash
cd ~/cachyos-hypr-noctalia
./update-repo.sh            # Sincroniza e reconstrói o pacote de release local
./update-repo.sh --commit   # Sincroniza e cria um commit no Git
./update-repo.sh --push     # Sincroniza, commita e envia (push) para o GitHub/GitLab
```

---

## 📁 Estrutura do Repositório

```text
├── bin/                 # Utilitários executáveis (ex: setup-audiorelay.sh universal)
├── color-schemes/       # Temas de cores (Noctalia)
├── configs/             # Dotfiles (~/.config)
│   ├── gtk-3.0/         # Estilos GTK 3 customizados
│   ├── gtk-4.0/         # Estilos GTK 4 customizados
│   ├── hypr/            # Configurações do Hyprland (Lua)
│   ├── kitty/           # Configurações do Terminal Kitty
│   ├── noctalia/        # Configurações da Shell Noctalia
│   ├── qt6ct/           # Tema Qt6 para integração KDE/Dolphin
│   ├── swash/           # Capturas de tela e utilitários
│   ├── systemd/         # Serviços de usuário (KDE Connect)
│   └── uwsm/            # Gerenciador de sessão Wayland
├── icons/               # Cursores (Bibata-Modern-Ice)
├── state/               # Estado e preferências do Noctalia (dock, opacidade, paletas)
├── wallpapers/          # Papéis de parede incluídos
├── build-release.sh     # Script para empacotar o tar.gz da Release
├── install.sh           # Instalador automatizado universal
├── sync-from-system.sh  # Sincronizador automático das configs do PC para o repositório
├── update-repo.sh       # Atalho para o sync-from-system.sh
└── README.md            # Esta documentação
```
