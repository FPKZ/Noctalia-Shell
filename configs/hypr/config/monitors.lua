-- Monitor wiki https://wiki.hypr.land/Configuring/Basics/Monitors/

if MONITOR1 and MONITOR1 ~= "" then
    hl.monitor({
        output    = MONITOR1,
        mode      = "preferred",
        position  = "0x0",
        scale     = "auto",
    })
end

if MONITOR2 and MONITOR2 ~= "" then
    hl.monitor({
        output    = MONITOR2,
        mode      = "preferred",
        position  = "auto-right",
        scale     = "auto",
    })
end

-- Regra universal / fallback para qualquer monitor novo, laptop ou tela desconectada:
hl.monitor({
    output    = "",
    mode      = "preferred",
    position  = "auto",
    scale     = "auto",
})
