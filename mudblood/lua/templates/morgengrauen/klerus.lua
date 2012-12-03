-- BETE
nmap("<F1>", "!pray()")
nmap("<E>gb", "!toggle_pray_mode()")

local pray_mode = 1
local pray_modes = {"andaechtig", "inbruenstig", "ausdauernd"}

function pray()
    sendln("bete " .. pray_modes[pray_mode+1])
end

function toggle_pray_mode()
    pray_mode = (pray_mode + 1) % #pray_modes
    print("Du betest jetzt " .. pray_modes[pray_mode+1])
end

-- LEBENSKRAFT
nmap("<F2>", "lebenskraft")

-- WEIHE
nmap("<F3>", "weihe")

-- HEILIGENSCHEIN
nmap("<F4>", "heiligenschein")

-- BLITZ UND DONNER
nmap("<F9>", "!sendln('steck waffe weg\\nblitz ' .. focus .. '\\nzueck waffe')")
nmap("<F10>", "donner")
nmap("<F11>", "!sendln('goetterzorn ' .. focus)")

-- HEILUNG
nmap("<F5>", "heile alle")
nmap("<F6>", "segne alle")

-- SPALTUNG
nmap("<F12>", "spaltung")

-- ELEMENTAR
nmap("<F7>", "!elementarsphaere()")
nmap("<E>ga", "!toggle_elementarsphaere()")
nmap("<F8>", "!elementarschild()")
nmap("<E>gs", "!toggle_elementarschild()")

local sphaere_mode = 1
local sphaere_modes = {"erde", "feuer", "eis", "wasser", "luft"}

function toggle_elementarsphaere()
    sphaere_mode = (sphaere_mode + 1) % #sphaere_modes
    print("Deine Elementarsphaere steht nun auf " .. sphaere_modes[sphaere_mode+1])
end

function elementarsphaere()
    sendln("elementarsphaere " .. sphaere_modes[sphaere_mode+1])
end

local schild_mode = 1
local schild_modes = {"erde", "feuer", "eis", "wasser", "luft", "saeure"}

function toggle_elementarschild()
    schild_mode = (schild_mode + 1) % #schild_modes
    print("Dein Elementarschild steht nun auf " .. schild_modes[schild_mode+1])
end

function elementarschild()
    sendln("elementarschild " .. schild_modes[schild_mode+1])
end
