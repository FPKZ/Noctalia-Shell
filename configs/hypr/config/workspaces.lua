-- Workspace rules wiki https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/
-- Regras dinâmicas para workspaces (adaptam-se a qualquer monitor conectado)
hl.workspace_rule({ workspace = "name:gaming", monitor = PRIMARY_MONITOR, default = true })
hl.workspace_rule({ workspace = "1", monitor = MONITOR1, default = true, persistent = true })
hl.workspace_rule({ workspace = "2", monitor = MONITOR1, default = true, persistent = true })
hl.workspace_rule({ workspace = "3", monitor = MONITOR1, default = true, persistent = true })

if MONITOR2 and MONITOR2 ~= "" then
    hl.workspace_rule({ workspace = "4", monitor = MONITOR2, default = true, persistent = true })
    hl.workspace_rule({ workspace = "5", monitor = MONITOR2, default = true, persistent = true })
    hl.workspace_rule({ workspace = "6", monitor = MONITOR2, default = true, persistent = true })
end
