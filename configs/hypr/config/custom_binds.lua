-- ==============================================================================
-- custom_binds.lua - Atalhos Personalizados do Usuário
-- Gerenciado automaticamente pelo Painel Gráfico de Atalhos ou editável manualmente.
-- As alterações aqui têm efeito imediato após salvar e rodar: hyprctl reload
-- ==============================================================================
local mainMod = "SUPER"
local launchPrefix = "uwsm app -- "

-- category: 🌌 Noctalia Shell
-- Central de Controle Noctalia (Home)
pcall(hl.unbind, mainMod .. " + Escape")
hl.bind(mainMod .. " + SUPER_L", hl.dsp.exec_cmd("noctalia msg panel-toggle control-center home"), { release = true })

