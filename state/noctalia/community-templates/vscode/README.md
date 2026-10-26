# VSCode

Generates Noctalia editor, syntax and semantic-token colors for VS Code, VSCodium and Antigravity IDE by replacing the color-theme file inside the Noctalia theme extension.

## Setup

1. Install the Noctalia theme extension (`noctalia.noctaliatheme`) in each editor you use: open the Extensions view (**Ctrl+Shift+X**), search for **NoctaliaTheme**, and click **Install**.
2. Select the theme: open the Command Palette (**Ctrl+Shift+P**), run **Preferences: Color Theme**, and pick **NoctaliaTheme**.
3. Enable **VSCode** in **Noctalia Settings -> Templates**.

The manifest targets extension version **0.0.5** at the exact paths below. It only checks for the editor's root directory, not whether the extension is installed. Generating the JSON alone does not install or register an extension. If your extension version or installation layout differs, adjust the template output path to match it.

## Output paths

- VS Code (requires `~/.vscode`): `~/.vscode/extensions/noctalia.noctaliatheme-0.0.5/themes/NoctaliaTheme-color-theme.json`
- VSCodium (requires `~/.vscode-oss`):
  - `~/.vscode-oss/extensions/noctalia.noctaliatheme-0.0.5-universal/themes/NoctaliaTheme-color-theme.json`
  - `~/.vscode-oss/extensions/noctalia.noctaliatheme-0.0.5/themes/NoctaliaTheme-color-theme.json`
- Antigravity IDE (requires `~/.antigravity-ide`): `~/.antigravity-ide/extensions/noctalia.noctaliatheme-0.0.5-universal/themes/NoctaliaTheme-color-theme.json`

These files are overwritten without backups; save any manual theme edits elsewhere. Extension updates can replace the generated file or change its path. No hook modifies editor settings or requests a reload: if new colors do not show up, run **Developer: Reload Window** from the Command Palette, or switch to another theme and back.
