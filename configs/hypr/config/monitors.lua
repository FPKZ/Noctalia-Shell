-- Monitor wiki https://wiki.hypr.land/Configuring/Basics/Monitors/
-- Exemplo: a saída de vídeo pode ser verificada com `hyprctl monitors`.
-- Para fixar resoluções ou taxas específicas, ajuste aqui ou via painel Noctalia / HVE.

-- Regra universal Plug & Play para qualquer monitor, laptop ou múltiplos displays:
hl.monitor({
    output    = "",
    mode      = "preferred",
    position  = "auto",
    scale     = "auto",
})
