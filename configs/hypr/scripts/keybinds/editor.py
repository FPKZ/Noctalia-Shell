"""
Módulo de Despacho de Editores de Texto e Código.
Princípio da Responsabilidade Única (SRP): gerenciar a abertura de arquivos em editores suportados.
"""
import os
import shutil
import subprocess

class EditorService:
    """Serviço para localizar e abrir arquivos no editor do usuário na linha solicitada."""

    SUPPORTED_EDITORS = [
        ("kwrite", lambda path, line: ["kwrite", "--line", str(line), path] if line > 0 else ["kwrite", path]),
        ("kate", lambda path, line: ["kate", "--line", str(line), path] if line > 0 else ["kate", path]),
        ("gnome-text-editor", lambda path, line: ["gnome-text-editor", f"+{line}", path] if line > 0 else ["gnome-text-editor", path]),
        ("code", lambda path, line: ["code", "-g", f"{path}:{line}"] if line > 0 else ["code", path]),
    ]

    @classmethod
    def get_command(cls, file_path: str, line_number: int = 0) -> list[str]:
        """Retorna o comando adequado para abrir o arquivo no editor disponível."""
        for name, cmd_builder in cls.SUPPORTED_EDITORS:
            if shutil.which(name):
                return cmd_builder(file_path, line_number)
        
        # Fallback terminal editor
        if line_number > 0:
            return ["kitty", "-e", "nano", f"+{line_number}", file_path]
        return ["kitty", "-e", "nano", file_path]

    @classmethod
    def open_file(cls, file_path: str, line_number: int = 0) -> bool:
        """Abre o arquivo no editor apropriado na linha indicada."""
        if not os.path.exists(file_path):
            return False
        cmd = cls.get_command(file_path, line_number)
        subprocess.Popen(cmd)
        return True

def open_file_in_editor(file_path: str, line_number: int = 0) -> bool:
    """Função utilitária de alto nível para compatibilidade direta."""
    return EditorService.open_file(file_path, line_number)
