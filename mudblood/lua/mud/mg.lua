local M = {}


M.stats = {
    lp = 0,
    lp_max = 0,
    lp_diff = 0,
    kp = 0,
    kp_max = 0,
    kp_diff = 0,
    vorsicht = 0,
    fluchtrichtung = "",
    gift = 0,
    taub = 0,
    frosch = 0,
    blind = 0,
    gesinnung = "",
    erfahrung = 0,
}

M.room = {}

M.base = {}
M.base.report = {}

local tlRecv = triggers.TriggerList.create()
local tlSend = triggers.TriggerList.create()
local tlTimer = triggers.TriggerList.create()

local function info(str)
    print(" " .. colors.Green .. str .. colors.Off)
end

------------------------------------------------------------------------------
-------------------- PUBLIC FUNCTIONS ----------------------------------------
------------------------------------------------------------------------------

function M.setup(guild, mm)
    M.mm = mm

    M.base.setup()

    if guild == "tanjian" then
        M.tanjian.setup()
    elseif guild == "klerus" then
        M.klerus.setup()
    end

    M.mapper.setup()
    M.team.setup()

    ctxGlobal.recvTriggers:add(tlRecv)
    ctxGlobal.sendTriggers:add(tlSend)
    ctxGlobal.timers:add(tlTimer)
end

function M.focus(name)
    if name then
        M.base.focus = name
    else
        return M.base.focus
    end
end

------------------------------------------------------------------------------
-------------------- CALLBACKS -----------------------------------------------
------------------------------------------------------------------------------

function M.base.onReport()
    if M.mm then
        print(string.format("LP: %d | KP: %d", M.stats.lp, M.stats.kp))
    else
        status(string.format("LP: %d | KP: %d", M.stats.lp, M.stats.kp))
    end
end

------------------------------------------------------------------------------
-------------------- GENERAL -------------------------------------------------
------------------------------------------------------------------------------

function M.base.setup()
    tlRecv:add(M.base.report.trigger2, "report", 200)
    tlRecv:add(M.base.fightTriggers, "fight")
    tlRecv:add(M.base.talkTriggers, "communication")

    M.onReport = M.base.onReport

    -- EOR telneg
    events.register("telneg", function (cmd, option, data)
        if cmd == telnet.WILL and option == telnet.DO_EOR then
            telnet.negDo(telnet.DO_EOR)
        elseif cmd == telnet.EOR then
            markPrompt()
        end
    end)

    nmap("<E>q", quit)
    nmap("<E>`", function () prompt("focus: ", function (f) M.focus(f); print("Fokus: " .. f) end) end)

    M.base.focus = ""
end

-- Report

M.base.report.trigger = triggers.line_func("MG Standard-Report", function (l)
    local changed = false
    string.gsub(l, "Du hast jetzt (%d+) Lebenspunkte.", function (d)
        M.stats.lp = tonumber(d)
        changed = true
    end)
    string.gsub(l, "Du hast jetzt (%d+) Konzentrationspunkte.", function (d)
        M.stats.kp = tonumber(d)
        changed = true
    end)
    if changed then
        M.onReport()
        return false
    end
    return nil
end)

M.base.report.trigger2 = triggers.gsub("LP: +(%d+), KP: +(%d+), Gift:", function (l, k)
    M.stats.lp = tonumber(l)
    M.stats.kp = tonumber(k)
    M.onReport()
    return false
end)

-- Spells

function M.base.spell(spell, hands, epilogue)
    if hands and hands > 0 then
        send("zieh schild aus")
        send("steck waffe weg")
    end

    print(colors.Yellow .. spell .. colors.Off)

    send(string.gsub(spell, "%%f", M.base.focus))

    if epilogue == true then
        send("zueck waffe")
        send("trage schild")
    elseif type(epilogue) == "string" then
        send(epilogue)
    end
end

------------------------------------------------------------------------------
-------------------- FARBEN --------------------------------------------------
------------------------------------------------------------------------------

M.base.talkTriggers = triggers.TriggerList.create()

-- Ebenen
M.base.talkTriggers:add(triggers.color_line("^%[[^%]]+:[^%]]+%]", colors.Blue))

-- Teile mit
M.base.talkTriggers:add(triggers.color_line("^%w+ teilt Dir mit: ", colors.Blue))
M.base.talkTriggers:add(triggers.color_line("^Dein Freund %w+ teilt Dir mit: ", colors.Blue))
M.base.talkTriggers:add(triggers.color_line("^Deine Freundin %w+ teilt Dir mit: ", colors.Blue))
M.base.talkTriggers:add(triggers.color_line("^.* aus der Ferne", colors.Blue))

M.base.fightTriggers = triggers.line_func("Attack", function (l)
    local attack = {
        {"verfehlst ([^%.]+)", 0, 0, ""},
        {"kitzelst (.+) am Bauch", 1, 1, "kitzelst"},
        {"kratzt ([^%.]+)", 2, 3, "kratzt"},
        {"triffst (.+) sehr hart", 11, 20, "triffst sehr hart"},
        {"triffst (.+) hart", 6, 10, "triffst hart"},
        {"triffst ([^%.]+)", 4, 5, "triffst"},
        {"schlaegst (.+) mit dem Krachen brechender Knochen", 21, 30, "krachst"},
        {"zerschmetterst (.+) in kleine Stueckchen", 31, 50, "schmetterst"},
        {"schlaegst (.+) zu Brei", 51, 75, "breist"},
        {"pulverisierst ([^%.]+)", 76, 100, "pulverst"},
        {"zerstaeubst ([^%.]+)", 101, 150, "zerstaeubst"},
        {"atomisierst ([^%.]+)", 151, 200, "atomisierst"},
        {"vernichtest ([^%.]+)", 201, 300, "vernichtest"},
    }

    for k,v in ipairs(attack) do
        local name = string.match(l, "^  Du " .. v[1])
        if name then
            if M.mm then
                if v[4] == "" then
                    return false, true
                else
                    return string.format("  Du %s %s.", v[4], name), true
                end
            else
                return colors.Green .. l .. " (" .. (v[2] == v[3] and v[2] or v[2] .. "-" .. v[3]) .. ")" .. colors.Off, true, false
            end
        end
    end

    local defense = {
        {"verfehlt Dich", 0, 0, ""},
        {"kitzelt Dich am Bauch", 1, 1, "kitzelt Dich"},
        {"kratzt Dich", 2, 3, "kratzt Dich"},
        {"trifft Dich sehr hart", 11, 20, "trifft dich sehr hart"},
        {"trifft Dich hart", 6, 10, "trifft Dich hart"},
        {"trifft Dich", 4, 5, "trifft Dich"},
        {"schlaegt Dich mit dem Krachen brechender Knochen", 21, 30, "kracht Dich"},
        {"zerschmettert Dich in kleine Stueckchen", 31, 50, "schmettert Dich"},
        {"schlaegt Dich zu Brei", 51, 75, "breit Dich"},
        {"pulverisiert Dich", 76, 100, "pulvert Dich"},
        {"zerstaeubt Dich", 101, 150, "zerstaeubt Dich"},
        {"atomisiert Dich", 151, 200, "atomisitert Dich"},
        {"vernichtet Dich", 201, 300, "vernichtet Dich"},
    }

    for k,v in ipairs(defense) do
        local name = string.match(l, "^  (.+) " .. v[1])
        if name then
            if M.mm then
                if v[4] == "" then
                    return false, true
                else
                    return string.format("  %s %s.", name, v[4]), true
                end
            else
                return colors.Red .. l .. " (" .. (v[2] == v[3] and v[2] or v[2] .. "-" .. v[3]) .. ")" .. colors.Off, true, false
            end
        end
    end

    return nil, false, false
end)

------------------------------------------------------------------------------
-------------------- MAPPING -------------------------------------------------
------------------------------------------------------------------------------

function M.room.blocker(direction, name)
    roomOnExit(direction, function ()
        directSend("knuddel " .. name)
        local ret = ctxRoom:wait({triggers.gsub("^Knuddle wen"),
                                  triggers.gsub("^Du knuddelst"),
                                  triggers.gsub("^Du kannst soviel ich weiss")})
        if ret == 2 then
            return false
        end
    end)
end

------------------------------------------------------------------------------
-------------------- MAPPER --------------------------------------------------
------------------------------------------------------------------------------

M.mapper = {}

M.mapper.mode = "fixed"
M.mapper.walklevel = 8
M.mapper.lastroom = map.room()

M.mapper.opposites = {
    n = "s",
    no = "sw",
    o = "w",
    so = "nw",
    s = "n",
    sw = "no",
    w = "o",
    nw = "so",
    ob = "u",
    u = "ob",
}

function M.mapper.setup()
    map.directions = {
        n = map.NORTH,
        no = map.NORTHEAST,
        o = map.EAST,
        so = map.SOUTHEAST,
        s = map.SOUTH,
        sw = map.SOUTHWEST,
        w = map.WEST,
        nw = map.NORTHWEST
    }

    tlSend:add(M.mapper.walkTrigger, "mapper", -200)

    events.register("room", function ()
        ctxRoom.reset()
        if map.room().getUserdata('script') ~= nil then
            cfun = assert(loadstring(map.room().getUserdata('script')))
            cfun()
        end
    end)

    mapper.pre_walk = function () directSend("ultrakurz") end
    mapper.post_walk = function () directSend("lang\nschau") end

    nmap("<E>f", function () prompt("fly: ", M.mapper.fly) end)
    nmap("<E>w", function () prompt("walk: ", M.mapper.walk) end)
    nmap("<E><TAB>b", M.mapper.walkBack)

    nmap("<E><TAB>d", function () prompt('walklevel: ', function (l) walk_level = tonumber(l) end) end)

    nmap("<E><TAB>mf", function () M.mapper.mode = "fixed"; info("mapper: Modus fixed") end)
    nmap("<E><TAB>ma", function () M.mapper.mode = "auto"; info("mapper: Modus auto") end)
    nmap("<E><TAB>mn", function () M.mapper.mode = "node"; info("mapper: Modus node") end)
    nmap("<E><TAB>mo", function () M.mapper.mode = "off"; info("mapper: Modus off") end)

    if M.mm then
        nmap("<E><TAB><TAB>", M.mapper.printRoomInfo)
    else
        nmap("<E><TAB><TAB>", function () map.visible = (not map.visible) end)
    end
end

M.mapper.walkTrigger = triggers.line_func("mapper", function (l)
    if M.mapper.mode == "off" or M.mapper.mode == "node" then
        return
    end

    local found = false
    for k,v in pairs(map.room().edges) do
        if l == k then
            v.to.fly()
            found = true
            break
        end
    end

    if found == false and mapper_mode == "auto" and opposites[l] ~= nil then
        local n = map.room().findNeighbor(l)
        if n then
            map.room().connect(n, l, opposites[l])
            info("mapper: Zyklus gefunden. Neue Kante gebaut.")
        else
            local newroom = map.addRoom()
            map.room().connect(newroom, l, opposites[l])
            newroom.fly()
            info("mapper: Neuen Raum gebaut.")
        end
    end
end)

function M.mapper.costFunction(r, e)
    if e.getUserdata('level') and e.getUserdata('level') >= M.mapper.walklevel then
        return -1
    else
        return e.weight
    end
end

function M.mapper.fly(r)
    map.room(r).fly()
    info("Flug erfolgreich.")
end

function M.mapper.walk(r)
    if M.mapper.mode == "off" then
        info("mapper: Kann nicht laufen, Mapper ist aus.")
    else
        if M.mapper.mode == "node" then
            M.mapper.mode = "fixed"
            M.mapper.lastroom = map.room()
            mapper.walk(map.room(r), M.mapper.costFunction)
            M.mapper.mode = "node"
        else
            M.mapper.lastroom = map.room()
            mapper.walk(map.room(r), M.mapper.costFunction)
        end
    end
end

function M.mapper.walkBack()
    local oldlast = map.room()
    M.mapper.walk(M.mapper.lastroom.id)
    M.mapper.lastroom = oldlast
end

function M.mapper.printRoomInfo()
    local edges = map.room().edges
    local ausg = ""
    if edges == {} then
        ausg = "Keine Ausgaenge."
    else
        local n = 0
        for k,v in pairs(edges) do
            n = n + 1
        end
        ausg = tostring(n) .. " Ausgaenge"
    end
    info(string.format("Raum #%d, Tag: %s. %s", map.room().id, (map.room().tag and map.room().tag or "keins"), ausg))
end

function M.mapper.printRoomInfoLong()
    info(string.format("Raum #%d, Tag: %s.", map.room().id, (map.room().tag and map.room().tag or "keins")))
    local edges = map.room().edges
    local ausg = ""
    if edges == {} then
        ausg = "Keine Ausgaenge."
    else
        for k,v in pairs(edges) do
            ausg = ausg .. k .. ", "
        end
    end
    info("Ausgaenge: " .. ausg)
end

------------------------------------------------------------------------------
-------------------- TEAMKAMPF -----------------------------------------------
------------------------------------------------------------------------------

M.team = {}

M.team.team = {}
M.team.tab = nil
M.team.fr = nil

function M.team.setup()
    tlRecv:add(M.team.recvTriggers, "team")
    tlSend:add(M.team.sendTriggers, "team")
end

function M.team.printStatus()
    local total = 0
    local ready = 0
    for k,v in pairs(M.team.team) do
        total = total + 1
        if v == true then
            ready = ready + 1
        end
    end
    info("TEAM: " .. tostring(ready) .. " von " .. tostring(total) .. " bereit.")
end

function M.team.show()
    local total = 0
    local ready = 0
    for k,v in pairs(M.team.team) do
        info(k .. " - " .. (v == true and "bereit" or "nicht bereit"))
    end
end

M.team.sendTriggers = triggers.TriggerList.create()
M.team.recvTriggers = triggers.TriggerList.create()

M.team.sendTriggers:add(triggers.gsub("^tab (.+)$", function (t)
    M.team.tab = t
end))

M.team.sendTriggers:add(triggers.gsub("^tab$", function (t)
    M.team.tab = nil
end))

M.team.sendTriggers:add(triggers.gsub("^fr (.+)$", function (t)
    M.team.fr = t
end))

M.team.sendTriggers:add(triggers.gsub("^fr$", function (t)
    M.team.fr = nil
end))

M.team.recvTriggers:add(triggers.gsub("(%w+) wurde ins Team aufgenommen", function (n)
    M.team.team[n] = false
end))

M.team.recvTriggers:add(triggers.gsub("(%w+) hat das Team verlassen", function (n)
    M.team.team[n] = nil
end))

M.team.recvTriggers:add(triggers.gsub("^(%w+) nickt", function (n)
    if M.team.team == {} then
        return
    end

    if M.team.team[n] == false then
        M.team.team[n] = true
    end
    M.team.printStatus()
end))

M.team.recvTriggers:add(triggers.gsub("%w+ startet den Angriff", function ()
    for k,v in pairs(M.team.team) do
        M.team.team[k] = false
    end
    if M.team.tab then
        local e = map.room().edges[M.team.tab]
        if e then
            e.to.fly()
        end
    end
end))

M.team.recvTriggers:add(triggers.gsub("Die Angst ist staerker als Du", function ()
    if M.team.fr then
        local e = map.room().edges[M.team.fr]
        if e then
            e.to.fly()
        end
    end
end))

------------------------------------------------------------------------------
-------------------- HORDE ---------------------------------------------------
------------------------------------------------------------------------------

M.horde = {}

M.horde.sendTriggers = triggers.TriggerList.create()

M.horde.follower = {}

function M.horde.setup()
    tlSend:add(M.horde.sendTriggers, "horde")
end

function M.horde.follow(name, p)
    M.horde.follower[name] = rpcClient("unix", p)
end

M.horde.sendTriggers:add(triggers.line_func("autofollow", function (l)
    for k,v in pairs(map.room().edges) do
        if l == k then
            if honda_follow then
                honda_rpc.send(k)
            end
        end
    end
end))

------------------------------------------------------------------------------
-------------------- TANJIAN -------------------------------------------------
------------------------------------------------------------------------------

M.tanjian = {}
M.tanjian.stats = {
    meditation = 0,
    kokoro = 0,
    tegatana = 0,
    hayai = 0,
    akshara = 0,
}
M.tanjian.spells = {}
M.tanjian.report = {}

-- Setup

function M.tanjian.setup()
    tlRecv:remove("report")
    tlRecv:add(M.tanjian.report.trigger, "report", 200)

    M.onReport = M.tanjian.onReport

    nmap('<F1>', M.tanjian.spells.meditation)
    nmap('<F2>', M.tanjian.spells.kokoro)
    nmap('<F3>', M.tanjian.spells.kami)
    --nmap('<F4>', M.tanjian.spells.kageodori)
    nmap('<F5>', M.tanjian.spells.tegatana)
    nmap('<F6>', M.tanjian.spells.omamori)
    nmap('<F7>', M.tanjian.spells.hayai)
    nmap('<F8>', M.tanjian.spells.akshara)
    nmap('<F9>', M.tanjian.spells.kaminari)
    nmap('<F10>', M.tanjian.spells.arashi)
    nmap('<F11>', M.tanjian.spells.samusa)
    nmap('<F12>', M.tanjian.spells.kshira)
end

function M.tanjian.onReport()
    if M.mm then
        info(string.format("LP: %d | KP: %d", M.stats.lp, M.stats.kp))
    else
        status(string.format("%d / %d | %d / %d | %d (%s) | %s %s %s %s %s %s %s %s | %s | %s | %d",
                    M.stats.lp, M.stats.lp_max, M.stats.kp, M.stats.kp_max, M.stats.vorsicht, M.stats.fluchtrichtung,
                    M.stats.gift == 1 and "G" or " ",
                    M.stats.blind == 1 and "B" or " ",
                    M.stats.taub == 1 and "T" or " ",
                    M.stats.frosch == 1 and "F" or " ",
                    M.tanjian.stats.hayai == 1 and "HA" or "  ",
                    M.tanjian.stats.tegatana == 1 and "TE" or (M.tanjian.stats.tegatana == 2 and "OM" or "  "),
                    M.tanjian.stats.kokoro == 1 and "KO" or "  ",
                    M.tanjian.stats.meditation == 1 and "M" or (M.tanjian.stats.meditation == 2 and "m" or " "),
                    M.tanjian.stats.akshara == 1 and "ja" or (M.tanjian.stats.akshara == 2 and "busy" or "nein"),
                    M.stats.gesinnung,
                    M.stats.erfahrung))
    end
end

-- Tanjianreport

M.tanjian.report.trigger = triggers.gsub("%$REPORT%$ (%d+) (%d+) (%d+) (%d+) (%d+) '(.+)' ([JN])([JN])([JN])([JN]) (%w+) ([%+%- ]) (%w+) (%w+) (%w+) ([JjN]) (%d+)", function (la, lm, ka, km, vo, fl, gi, bl, ta, fr, ko, te, ha, ak, ca, me, ep)
    M.stats.lp_diff = tonumber(la) - M.stats.lp
    M.stats.lp = tonumber(la)
    M.stats.lp_max = tonumber(lm)

    M.stats.kp_diff = tonumber(ka) - M.stats.kp
    M.stats.kp = tonumber(ka)
    M.stats.kp_max = tonumber(km)

    M.stats.vorsicht = tonumber(vo)
    M.stats.fluchtrichtung = fl

    if gi == "J" then M.stats.gift = 1 else gift = 0 end
    if bl == "J" then M.stats.blind = 1 else blind = 0 end
    if ta == "J" then M.stats.taub = 1 else taub = 0 end
    if fr == "J" then M.stats.frosch = 1 else frosch = 0 end
    
    if ko == "ja" then M.tanjian.stats.kokoro = 1 else M.tanjian.stats.kokoro = 0 end
    if te == "+" then M.tanjian.stats.tegatana = 1 elseif te == "-" then M.tanjian.stats.tegatana = 2 else M.tanjian.stats.tegatana = 0 end
    if ha == "ja" then M.tanjian.stats.hayai = 1 else M.tanjian.stats.hayai = 0 end
    if ak == "ja" then M.tanjian.stats.akshara = 1 elseif ak == "busy" then M.tanjian.stats.akshara = 2 else M.tanjian.stats.akshara = 0 end
    if me == "J" then M.tanjian.stats.meditation = 1 elseif me == "j" then M.tanjian.stats.meditation = 2 else M.tanjian.stats.meditation = 0 end
    
    M.stats.gesinnung = ca
    M.stats.erfahrung = ep

    M.onReport()

    return false
end)

-- Spells

function M.tanjian.spells.meditation()
    M.base.spell("meditation")
end

function M.tanjian.spells.kokoro()
    M.base.spell("kokoro")
end

function M.tanjian.spells.tegatana()
    M.base.spell("tegatana")
end

function M.tanjian.spells.omamori()
    M.base.spell("omamori")
end

function M.tanjian.spells.hayai()
    M.base.spell("hayai")
end

function M.tanjian.spells.akshara()
    M.base.spell("akshara")
end

function M.tanjian.spells.koryoku()
    M.base.spell("koryoku %f")
end

function M.tanjian.spells.kaminari()
    M.base.spell("kaminari %f")
end

function M.tanjian.spells.arashi()
    M.base.spell("arashi %f")
end

function M.tanjian.spells.samusa()
    M.base.spell("samusa %f")
end

function M.tanjian.spells.kshira()
    M.base.spell("kshira %f")
end

function M.tanjian.spells.kami()
    M.base.spell("kami %f")
end


------------------------------------------------------------------------------
-------------------- KLERIKER ------------------------------------------------
------------------------------------------------------------------------------

M.klerus = {}

M.klerus.spells = {}

function M.klerus.setup()
    nmap("<F1>", M.klerus.spells.heiligenschein)
    nmap("<F2>", M.klerus.spells.weihe)
    nmap("<F3>", M.klerus.spells.frieden)
    nmap("<F4>", M.klerus.spells.lebenskraft)

    nmap("<F5><F1>", function () M.klerus.spells.elementarschild("erde") end)
    nmap("<F5><F2>", function () M.klerus.spells.elementarschild("feuer") end)
    nmap("<F5><F3>", function () M.klerus.spells.elementarschild("eis") end)
    nmap("<F5><F4>", function () M.klerus.spells.elementarschild("wasser") end)
    nmap("<F5><F5>", function () M.klerus.spells.elementarschild("luft") end)
    nmap("<F5><F6>", function () M.klerus.spells.elementarschild("saeure") end)

    nmap("<F6><F1>", function () M.klerus.spells.elementarsphaere("erde") end)
    nmap("<F6><F2>", function () M.klerus.spells.elementarsphaere("feuer") end)
    nmap("<F6><F3>", function () M.klerus.spells.elementarsphaere("eis") end)
    nmap("<F6><F4>", function () M.klerus.spells.elementarsphaere("wasser") end)
    nmap("<F6><F5>", function () M.klerus.spells.elementarsphaere("luft") end)
    nmap("<F6><F6>", function () M.klerus.spells.elementarsphaere("saeure") end)

    nmap("<F7>", M.klerus.spells.goettermacht)

    nmap("<F9>", M.klerus.spells.blitz)
    nmap("<F10>", M.klerus.spells.goetterzorn)
    nmap("<F11>", M.klerus.spells.erloese)
    nmap("<F12>", M.klerus.spells.donner)
end

-- Spells

function M.klerus.spells.heiligenschein()
    M.base.spell("heiligenschein")
end

function M.klerus.spells.lebenskraft()
    M.base.spell("lebenskraft")
end

function M.klerus.spells.blitz()
    M.base.spell("blitz %f", 2, true)
end

function M.klerus.spells.donner()
    M.base.spell("donner %f")
end

function M.klerus.spells.erloese()
    M.base.spell("erloese %f", 2, true)
end

function M.klerus.spells.elementarsphaere(element)
    M.base.spell("elementarsphaere " .. element)
end

function M.klerus.spells.elementarschild(element)
    M.base.spell("elementarschild " .. element)
end

function M.klerus.spells.goettermacht()
    M.base.spell("goettermacht")
end

function M.klerus.spells.weihe()
    M.base.spell("weihe")
end

function M.klerus.spells.frieden()
    M.base.spell("frieden")
end

function M.klerus.spells.goetterzorn()
    M.base.spell("goetterzorn %f")
end

return M
