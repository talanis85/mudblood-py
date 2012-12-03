require "string"
require "table"
require "os"

-- Verfassung
triggers.user:add(triggers.line_func("Defense", function (l)
    local constitution = {
        {"ist absolut fit", "100"},
        {"ist schon etwas geschwaecht", "90"},
        {"fuehlte sich heute schon besser", "80"},
        {"ist leicht angeschlagen", "70"},
        {"sieht nicht mehr taufrisch aus", "60"},
        {"macht einen mitgenommenen Eindruck", "50"},
        {"wankt bereits bedenklich", "40"},
        {"ist in keiner guten Verfassung", "30"},
        {"braucht dringend einen Arzt", "20"},
        {"steht auf der Schwelle des Todes", "10"},
    }

    for k,v in ipairs(constitution) do
        if string.find(l, v[1] .. "%.$") then
            return l .. " (" .. v[2] .. "%)", true, false
        end
    end

    return nil, false, false
end))

lp = 0
lp_max = 0
kp = 0
kp_max = 0
vorsicht = 0
fluchtrichtung = 0
gift = 0
blind = 0
taub = 0
frosch = 0
erfahrung = 0

local function report_default()
    setstatus("LP: " .. tostring(lp) .. " | KP: " .. tostring(kp))
end

-- Report 1
triggers.user:add(triggers.line_func("Report", function (l)
    local changed = false
    string.gsub(l, "Du hast jetzt (%d+) Lebenspunkte.", function (d)
        lp = tonumber(d)
        changed = true
    end)
    string.gsub(l, "Du hast jetzt (%d+) Konzentrationspunkte.", function (d)
        kp = tonumber(d)
        changed = true
    end)
    if changed then
        if type(report) == "function" then
            report()
        else
            report_default()
        end
        return ""
    end
    return nil
end), -200)

-- Report 2 (alt?)
triggers.user:add(triggers.gsub("LP: +(%d+), KP: +(%d+), Gift:", function (l, k)
    lp = tonumber(l)
    kp = tonumber(k)
    if type(report) == "function" then
        report()
    else
        report_default()
    end
    return ""
end))

-- SPELLS

nmap('<E>`', '!prompt("focus: ", function (f) focus = f end)')

focus = ""

function spell(s, freehands)
    if freehands == true then
        send("steck waffe weg\nzieh schild aus\n")
    end

    if focus == "" then
        send(s .. "\n")
        print(s)
    else
        send(s .. " " .. focus .. "\n")
        print(s .. " " .. focus)
    end
end

-- KEY BINDINGS

nmap("<E>q", "!quit()")

nmap('<E>w', '!prompt("walk: ", mapper.walk)')
nmap('<E>f', '!prompt("fly: ", function (r) map.room(r):fly() end)')

nmap('<E>l', '!lp_track_toggle()')

nmap('<E><TAB><TAB>', '!map.toggle()')
nmap('<E><TAB>mo', '!map.mode(0)')
nmap('<E><TAB>mf', '!map.mode(1)')
nmap('<E><TAB>ma', '!map.mode(2)')
nmap('<E><TAB>mr', '!map.mode(3)')
nmap('<E><TAB>r', '!prompt("remove exit: ", function (e) map.room():edges()[e]:disconnect() end)')
--nmap('<E><TAB>o', '!prompt("<oldname>,<newname>: ", mapping.opposite)')
nmap('<E><TAB>t', '!prompt("tag: ", function (t) map.room():tag(t) end)')
nmap('<E><TAB>b', '!mapper.walk_back()')
--nmap('<E><TAB>d', '!prompt("danger: ", mapper.set_danger)')
nmap('<E><TAB>D', '!prompt("set braveness: ", function (b) mapper.braveness = b end)')

-- COPYPASTE

nmap('<E>c', '!visual(function (d) copypaste.exec("xclip -i", d) end)')
nmap('<E>v', '!copypaste.paste()')

nmap('<E>af', '!visual(copypaste.follow_link)')

-- ROOM SCRIPT

nmap('<E>se', '!map.room():script(editor(map.room():script()))')

connect("mg.mud.de", 4711)

