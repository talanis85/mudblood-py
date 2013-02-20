--- Help system.
-- @module help
-- @alias M
local M = {}

require "io"
require "table"

local function ask(question)
    local ret

    print(" " .. question)

    _, ret = ctxGlobal:waitSend({triggers.any("input prompt")})

    return ret
end

local function more()
    ask("ENTER to continue")
end

M.tutorial = triggers.coroutine(function ()
    local name, template

    print([[
Willkommen bei mudblood!

Mudblood ist ein funktionsreicher und sehr flexibler Client fuer textbasierte MUDs aller Art.
Dieses Tutorial versucht Dir den Einstieg in dieses Programm leichter machen.
]])

    more()

    print([[
1. BEDIENKONZEPT

Es gibt eine Vielzahl verschiedener MUDs im Internet. Und es gibt noch viel mehr individuelle
Spieler. Um diesem Umstand Rechnung zu tragen, ist das Ziel von mudblood, so frei konfigurierbar
wie moeglich zu sein.

Desweiteren verzichtet mudblood vollstaendig auf Mausunterstuetzung. Jegliche Bedienung erfolgt
ueber die Tastatur. Im Folgenden werden wir sehen, wie das geht.
]])

    more()

end)

return M
