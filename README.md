# 🌌 CachyOS: Hyprland + Noctalia Shell (Setup Portátil & Universal)

Setup completo, estável e portátil para **CachyOS / Arch Linux**, unindo o poder do compositor **Hyprland** com a elegância do **Noctalia Shell**, projetado para coexistir perfeitamente lado a lado com o **KDE Plasma** sem nenhum conflito de pacotes ou configurações.

---

## ✨ Recursos e Ajustes Incluídos

- ⌨️ **Teclado PT-BR ABNT2 Nativo:** Configurado diretamente em `inputs.lua` e sincronizado com o compositor.
- 📜 **Cheatsheet Interativo de Teclas:** Pressione `Super + F1` ou `Super + /` para abrir um menu pesquisável com todos os atalhos do sistema.
- 💾 **Restauração de Sessão Automática:** Script em segundo plano (`session.py`) que salva periodicamente as janelas e seus respectivos workspaces, restaurando-os silenciosamente após reiniciar o PC.
- 🎨 **Consistência Visual do Dolphin / Apps KDE:** Integração via `qt6ct` e `noctalia.colors`. O Dolphin abre no modo escuro perfeito sem bugs de contraste ou fundo branco.
- ⚡ **Eliminação de Piscadas no Boot (Early KMS):** O script instalador detecta automaticamente se a sua GPU é **AMD (`amdgpu`)**, **NVIDIA (`nvidia`)** ou **Intel (`i915`)** e injeta o módulo correto no `mkinitcpio.conf`.
- 🔊 **AudioRelay Universal:** Script dinâmico em PipeWire (`setup-audiorelay.sh`) que detecta a placa de som padrão de qualquer PC e cria o canal de espelhamento e microfone virtual sem alterar seus dispositivos físicos.
- 📱 **KDE Connect Integrado:** Serviço de usuário em segundo plano gerenciado pelo systemd com regras de firewall abertas por padrão.
- 💻 **Terminal Kitty & Fish:** Configurado com `xterm-256color` e alias `ssh = kitten ssh` para conexões remotas sem quebra do comando `clear`.
- 🖥️ **Monitores Dinâmicos:** Configuração universal adaptável a qualquer resolução e taxa de atualização (single ou multi-monitor).

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

## 📁 Estrutura do Repositório

```text
├── applications/        # Lançadores .desktop ajustados (ex: Dolphin)
├── bin/                 # Utilitários executáveis (ex: setup-audiorelay.sh universal)
├── color-schemes/       # Temas de cores (Noctalia)
├── configs/             # Dotfiles (~/.config)
│   ├── hypr/            # Configurações do Hyprland (Lua)
│   ├── kitty/           # Configurações do Terminal Kitty
│   ├── noctalia/        # Configurações da Shell Noctalia
│   ├── qt6ct/           # Tema Qt6 para integração KDE/Dolphin
│   ├── swash/           # Wallpaper e temas
│   ├── systemd/         # Serviços de usuário (KDE Connect)
│   └── uwsm/            # Gerenciador de sessão Wayland
├── icons/               # Cursores (Bibata-Modern-Ice)
├── build-release.sh     # Script para empacotar o tar.gz da Release
├── install.sh           # Instalador automatizado universal
└── README.md            # Esta documentação
```
