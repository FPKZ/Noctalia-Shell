-- Monitor wiki https://wiki.hypr.land/Configuring/Basics/Monitors/

hl.monitor({
    output    = MONITOR1,
    mode      = "1920x1080@100",
    position  = "0x0",
    scale     = "1",
})

hl.monitor({
    output    = MONITOR2,
    mode      = "1920x1080@74.97",
    position  = "1920x0",
    scale     = "1",
})

-- Regra universal / fallback para qualquer monitor novo, laptop ou tela desconectada:
hl.monitor({
    output    = "",
    mode      = "preferred",
    position  = "auto",
    scale     = "auto",
})
