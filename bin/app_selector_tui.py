#!/usr/bin/env python3
# ==============================================================================
# bin/app_selector_tui.py
# Interface de Terminal Moderna e Nativa para Seleção de Aplicativos
# 100% Integrada às Cores, Fontes e Transparência do Kitty / Terminal
# ==============================================================================
import sys
import os
import tty
import termios
import argparse
import select
import shutil

# Cores ANSI harmoniosas (estilo Material You / Noctalia)
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_BORDER = "\033[38;2;140;140;180m"
C_TITLE = "\033[1;38;2;196;134;220m"
C_HIGHLIGHT = "\033[1;38;2;225;190;231m"
C_CHECKED = "\033[1;38;2;129;199;132m"
C_UNCHECKED = "\033[2;37m"
C_ACCENT = "\033[38;2;186;104;200m"

def get_key(fd: int) -> str:
    """Lê tecla ou sequência de escape do teclado de forma instantânea e sem buffering."""
    try:
        c1 = os.read(fd, 1)
    except Exception:
        return 'QUIT'

    if not c1:
        return 'QUIT'

    # Sequências ANSI / Escape
    if c1 == b'\x1b':
        r, _, _ = select.select([fd], [], [], 0.05)
        if r:
            c2 = os.read(fd, 1)
            if c2 in (b'[', b'O'):
                c3 = os.read(fd, 1)
                if c3 == b'A': return 'UP'
                if c3 == b'B': return 'DOWN'
                if c3 == b'C': return 'RIGHT'
                if c3 == b'D': return 'LEFT'
                if c3 == b'H': return 'HOME'
                if c3 == b'F': return 'END'
                if c3 in (b'1', b'2', b'3', b'4', b'5', b'6'):
                    r2, _, _ = select.select([fd], [], [], 0.02)
                    c4 = os.read(fd, 1) if r2 else b''
                    if c3 == b'5' and c4 == b'~': return 'PAGEUP'
                    if c3 == b'6' and c4 == b'~': return 'PAGEDOWN'
                    if c3 == b'1' and c4 == b'~': return 'HOME'
                    if c3 == b'4' and c4 == b'~': return 'END'
                return 'ESC'
            return 'ESC'
        return 'ESC'

    if c1 in (b'\r', b'\n'): return 'ENTER'
    if c1 in (b' ', b'\t'): return 'SPACE'
    if c1 in (b'q', b'Q', b'\x03'): return 'QUIT'
    if c1 in (b'a', b'A'): return 'ALL'
    if c1 in (b'k', b'K'): return 'UP'
    if c1 in (b'j', b'J'): return 'DOWN'

    try:
        return c1.decode('utf-8', errors='ignore')
    except Exception:
        return ''

def clear_lines(count: int):
    """Limpa as linhas anteriormente renderizadas no terminal."""
    if count <= 0:
        return
    sys.stdout.write(f"\033[{count}A\r")
    for _ in range(count):
        sys.stdout.write("\033[2K\n")
    sys.stdout.write(f"\033[{count}A\r")
    sys.stdout.flush()

def run_tui(title: str, prompt: str, items: list[dict], out_file: str) -> int:
    """Executa a interface interativa no terminal."""
    if not sys.stdin.isatty():
        # Modo não-interativo: grava todos com checked=True
        with open(out_file, 'w', encoding='utf-8') as f:
            for it in items:
                if it['checked']:
                    f.write(f"{it['tag']}\n")
        return 0

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    cursor_idx = 0
    window_top = 0
    total_items = len(items)
    page_size = 12

    try:
        tty.setcbreak(fd)
        # Ocultar cursor
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

        first_render = True
        total_rendered_lines = 0

        while True:
            # Manter janela de visualização suave
            if cursor_idx < window_top:
                window_top = cursor_idx
            elif cursor_idx >= window_top + page_size:
                window_top = cursor_idx - page_size + 1

            start_idx = window_top
            end_idx = min(start_idx + page_size, total_items)

            # Voltar cursor para o topo do bloco anterior
            if not first_render and total_rendered_lines > 0:
                sys.stdout.write(f"\033[{total_rendered_lines}A\r")

            term_cols = shutil.get_terminal_size((80, 24)).columns
            width = min(max(term_cols - 4, 50), 76)

            sep_line = f"{C_BORDER}├{'─' * (width - 2)}┤{C_RESET}"
            top_line = f"{C_BORDER}╭{'─' * (width - 2)}╮{C_RESET}"
            bot_line = f"{C_BORDER}╰{'─' * (width - 2)}╯{C_RESET}"

            lines = []
            lines.append(top_line)
            title_text = f" {title} "[:width - 4]
            lines.append(f"{C_BORDER}│{C_RESET} {C_TITLE}{title_text:<{width - 4}}{C_RESET} {C_BORDER}│{C_RESET}")
            lines.append(sep_line)

            # Itens visíveis
            tag_width = 18
            for i in range(start_idx, end_idx):
                item = items[i]
                is_cur = (i == cursor_idx)
                is_chk = item['checked']

                arrow = f"{C_HIGHLIGHT}❯{C_RESET}" if is_cur else " "
                mark = f"{C_CHECKED}[●]{C_RESET}" if is_chk else f"{C_UNCHECKED}[ ]{C_RESET}"
                
                tag_display = item['tag'][:tag_width]
                tag_str = f"{C_BOLD}{tag_display:<{tag_width}}{C_RESET}" if is_cur else f"{tag_display:<{tag_width}}"

                # Espaço restante para descrição
                # Estrutura: "│ " (2) + arrow (1) + " " (1) + mark (3) + " " (1) + tag_str (tag_width) + " " (1) + desc + padding + " │" (2)
                max_desc_len = max(0, width - 4 - 1 - 1 - 3 - 1 - tag_width - 1)
                desc_text = item['desc'][:max_desc_len]
                desc_str = f"{C_DIM}{desc_text}{C_RESET}"

                content = f"{arrow} {mark} {tag_str} {desc_str}"
                visible_len = 1 + 1 + 3 + 1 + tag_width + 1 + len(desc_text)
                padding = max(0, width - 4 - visible_len)
                lines.append(f"{C_BORDER}│{C_RESET} {content}{' ' * padding} {C_BORDER}│{C_RESET}")

            # Indicador de posição / contagem
            selected_count = sum(1 for it in items if it['checked'])
            scroll_info = f" ({cursor_idx + 1}/{total_items}) • {selected_count} selecionado(s) "
            lines.append(f"{C_BORDER}│{C_RESET} {C_ACCENT}{scroll_info:^{width - 4}}{C_RESET} {C_BORDER}│{C_RESET}")
            lines.append(sep_line)

            # Rodapé informativo com atalhos
            hint = "[↑/↓] Navegar • [Espaço] Marcar • [A] Todos • [Enter] Salvar • [Esc] Sair"
            hint_short = "[↑/↓] Navegar • [Espaço] Marcar • [Enter] Salvar • [Esc] Sair"
            chosen_hint = hint if len(hint) <= (width - 4) else hint_short
            lines.append(f"{C_BORDER}│{C_RESET} {C_DIM}{chosen_hint:^{width - 4}}{C_RESET} {C_BORDER}│{C_RESET}")
            lines.append(bot_line)

            total_rendered_lines = len(lines)
            first_render = False

            # Imprimir o bloco
            for line in lines:
                sys.stdout.write(f"\033[2K{line}\n")
            sys.stdout.flush()

            # Capturar tecla do usuário
            key = get_key(fd)

            if key in ('UP', 'k', 'K'):
                if cursor_idx > 0:
                    cursor_idx -= 1
                else:
                    cursor_idx = total_items - 1
            elif key in ('DOWN', 'j', 'J'):
                if cursor_idx < total_items - 1:
                    cursor_idx += 1
                else:
                    cursor_idx = 0
            elif key == 'PAGEUP':
                cursor_idx = max(0, cursor_idx - page_size)
            elif key == 'PAGEDOWN':
                cursor_idx = min(total_items - 1, cursor_idx + page_size)
            elif key == 'HOME':
                cursor_idx = 0
            elif key == 'END':
                cursor_idx = total_items - 1
            elif key == 'SPACE':
                items[cursor_idx]['checked'] = not items[cursor_idx]['checked']
            elif key == 'ALL':
                all_checked = all(it['checked'] for it in items)
                for it in items:
                    it['checked'] = not all_checked
            elif key == 'ENTER':
                # Limpar interface e exibir confirmação elegante
                clear_lines(total_rendered_lines)
                with open(out_file, 'w', encoding='utf-8') as f:
                    for it in items:
                        if it['checked']:
                            f.write(f"{it['tag']}\n")
                sys.stdout.write(f"{C_CHECKED}✔{C_RESET} {C_BOLD}{title}:{C_RESET} {selected_count} aplicativo(s) selecionado(s).\n")
                sys.stdout.flush()
                return 0
            elif key in ('ESC', 'QUIT'):
                # Limpar interface e sair com código 130
                clear_lines(total_rendered_lines)
                return 130

    except KeyboardInterrupt:
        clear_lines(total_rendered_lines)
        return 130
    finally:
        # Restaurar cursor e configurações do terminal
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def main():
    parser = argparse.ArgumentParser(description="Terminal Checklist TUI")
    parser.add_argument("--title", default="Seleção de Aplicativos")
    parser.add_argument("--prompt", default="Selecione os aplicativos desejados:")
    parser.add_argument("--out", required=True, help="Arquivo para salvar os selecionados")
    parser.add_argument("raw_items", nargs="*", help="Tuplas: TAG DESC STATUS")

    args = parser.parse_args()

    items = []
    i = 0
    raw = args.raw_items
    while i < len(raw):
        tag = raw[i]
        desc = raw[i+1] if (i+1) < len(raw) else tag
        status = raw[i+2] if (i+2) < len(raw) else "OFF"
        items.append({
            'tag': tag,
            'desc': desc,
            'checked': (status.upper() == "ON")
        })
        i += 3

    if not items:
        with open(args.out, 'w') as f:
            pass
        return 0

    code = run_tui(args.title, args.prompt, items, args.out)
    sys.exit(code)

if __name__ == "__main__":
    main()
