-- CachyOS Hyprland Configuration

require("config.animations")
require("config.autostart")
require("config.colors")
require("config.decorations")
require("config.variables")
require("config.environment")
require("config.inputs")
require("config.binds")
require("config.misc")
require("config.monitors")
require("config.windowrules")
require("config.workspaces")

-- >>> HYPRLAND VISUAL EDITOR (HVE) <<<
pcall(function() dofile(os.getenv("HOME") .. "/.cache/noctalia/HVE/overlay.lua") end)
-- <<< HYPRLAND VISUAL EDITOR (HVE) <<<

-- For Noctalia Color templates
require("noctalia").apply_theme()

-- Noctalia Hyprland Settings Plugin: carregado no final para que as configurações
-- personalizadas do usuário no painel do Noctalia (Displays/Telas, Aparência, Input)
-- tenham prioridade e alterem a tela imediatamente.
require("hyprland-settings")
