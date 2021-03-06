local M = {}


M.stats = {
    name = "Jemand",
    guild = "Abenteurer",
    race = "Mensch",
    presay = "",
    title = "",
    wizlevel = 0,
    level = 1,
    guildlevel = 1,
    guildtitle = "",

    lp = 0,
    lp_max = 0,
    lp_diff = 0,
    kp = 0,
    kp_max = 0,
    kp_diff = 0,
    vorsicht = 0,
    fluchtrichtung = "",
    gift = 0,
    gift_max = 1,
    taub = 0,
    frosch = 0,
    blind = 0,
    gesinnung = "",
    erfahrung = 0,
    a_con = 0,
    a_int = 0,
    a_dex = 0,
    a_str = 0
}

M.room = {}

M.base = {}
M.base.report = {}

M.keyprefix = "<E>"

local tlRecv = triggers.TriggerList.create()
local tlSend = triggers.TriggerList.create()
local tlTimer = triggers.TriggerList.create()

local tlRecvVolatile = triggers.TriggerList.create()

local function info(str)
    print(" " .. colors.Green .. str .. colors.Off)
end

nmap("`", function ()
    prompt("lua: ", function (l)
        loadstring(l)()
    end)
end)

------------------------------------------------------------------------------
-------------------- PUBLIC FUNCTIONS ----------------------------------------
------------------------------------------------------------------------------

--{{{
function M.setup(guild, prefix, seer, mm)
    M.mm = mm
    M.keyprefix = prefix

    if seer == true then
        M.seer = true
    else
        M.seer = false
    end

    M.base.setup()

    if guild == "tanjian" then
        M.tanjian.setup()
    elseif guild == "klerus" or guild == "kleriker" then
        M.klerus.setup()
    elseif guild == "kaempfer" or guild == "trves" then
        M.kaempfer.setup()
    end

    M.mapper.setup()
    M.team.setup()

    ctxGlobal.recvTriggers:add(tlRecv)
    ctxGlobal.sendTriggers:add(tlSend)
    ctxGlobal.timers:add(tlTimer)

    ctxGlobal.recvTriggers:add(tlRecvVolatile)
end

function M.focus(name)
    if name then
        M.base.focus = name
    else
        return M.base.focus
    end
end

function M.addvolatile(t)
    tlRecvVolatile:add(t)
end
--}}}

------------------------------------------------------------------------------
-------------------- CALLBACKS -----------------------------------------------
------------------------------------------------------------------------------

--{{{
function M.base.onReport()
    if M.mm then
        print(string.format("%s (%s) | %d / %d | %d / %d | v:%d (%s) | g:%d/%d",
                    M.stats.name, M.stats.guild,
                    M.stats.lp, M.stats.lp_max, M.stats.kp, M.stats.kp_max,
                    M.stats.vorsicht, M.stats.fluchtrichtung,
                    M.stats.gift, M.stats.gift_max))
    else
        M.base.status.report = string.format("%s (%s) | %d / %d | %d / %d | v:%d (%s) | g:%d/%d",
                    M.stats.name, M.stats.guild,
                    M.stats.lp, M.stats.lp_max, M.stats.kp, M.stats.kp_max,
                    M.stats.vorsicht, M.stats.fluchtrichtung,
                    M.stats.gift, M.stats.gift_max)
        M.base.status.update()
    end
end
--}}}

------------------------------------------------------------------------------
-------------------- GENERAL -------------------------------------------------
------------------------------------------------------------------------------

--{{{
function M.base.setup()
    tlRecv:add(M.base.report.trigger2, "report", 200)
    tlRecv:add(M.base.fightTriggers, "fight")
    tlRecv:add(M.base.talkTriggers, "communication")
    tlRecv:add(M.base.fitnessTrigger, "fitness")

    M.onReport = M.base.onReport

    -- Telnegs
    events.register("telneg", function (cmd, option, data)
        print("Telneg: cmd=" .. tostring(cmd) .. ", option=" .. tostring(option) .. ", data=" .. tostring(data), "telnet")
        if cmd == telnet.WILL and option == telnet.OPT_EOR then
            telnet.negDo(telnet.OPT_EOR)
        elseif cmd == telnet.WILL and option == 201 then
            M.gmcp.setup()
        elseif cmd == telnet.EOR then
            tlRecvVolatile:clear()
            markPrompt()
        end
    end)

    -- Logging
    M.base.logfd = assert(io.open(path.profile() .. "/log", "a"))

    tlRecv:add(M.base.recvLogger, "logger", -1000)
    tlSend:add(M.base.sendLogger, "logger", -1000)

    nmap(M.keyprefix .. "q", quit)
    nmap(M.keyprefix .. "`", function () prompt("focus: ", function (f) M.focus(f); info("Fokus: " .. f) end) end)

    M.base.focus = ""
end

-- Log

M.base.recvLogger = triggers.line_func("Logger", function (l)
    if mapper.walking() then
        return nil
    end

    if M.base.logfd ~= nil then
        M.base.logfd:write(stripColors(l) .. "\n")
        M.base.logfd:flush()
    end
end)

M.base.sendLogger = triggers.line_func("Logger", function (l)
    if mapper.walking() then
        return nil
    end

    if M.base.logfd ~= nil then
        M.base.logfd:write("> " .. stripColors(l) .. "\n")
        M.base.logfd:flush()
    end
end)

-- Status lines
M.base.status = {}
M.base.status.report = ""
M.base.status.mapper = ""

function M.base.status.update()
    padding = ""
    for i=0,(screen.width() - #M.base.status.report - 53) do
        padding = padding .. " "
    end

    status(string.format("%s%-10.10s %s#%-5.5d %s%-10.10s %s%-20.20s%s %s",
                         colors.Red,                        M.mapper.mode,
                         colors.Green,                      map.room().id,
                         colors.Red,                        map.room().getUserdata("tag"),
                         colors.Green,                      map.room().getUserdata("hash"),
                         colors.Off .. padding,             M.base.status.report))
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

    realspell = string.gsub(spell, "%%f", M.base.focus)
    print(colors.Yellow .. realspell .. colors.Off)

    send(realspell)

    if epilogue == true then
        send("zueck waffe")
        send("trage schild")
    elseif type(epilogue) == "string" then
        send(epilogue)
    end
end

M.base.fitnessTrigger = triggers.line_func("Defense", function (l)
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
end)
--}}}

------------------------------------------------------------------------------
-------------------- GMCP ----------------------------------------------------
------------------------------------------------------------------------------

--{{{
M.gmcp = {}
M.gmcp.active = false

function M.gmcp.setup()
    events.register("gmcp", function (mod, data)
        if mod == "MG.char.base" then
            M.stats.name = data['name']
            M.stats.guild = data['guild']
            M.stats.race = data['race']
            M.stats.presay = data['presay']
            M.stats.title = data['title']
            M.stats.wizlevel = data['wizlevel']
        elseif mod == "MG.char.info" then
            M.stats.level = data['level']
            M.stats.guildlevel = data['guild_level']
            M.stats.guildtitle = data['guild_title']
        elseif mod == "MG.char.maxvitals" then
            M.stats.lp_max = data['max_hp']
            M.stats.kp_max = data['max_sp']
            M.stats.gift_max = data['max_poison']
        elseif mod == "MG.char.attributes" then
            M.stats.a_con = data['con']
            M.stats.a_int = data['int']
            M.stats.a_dex = data['dex']
            M.stats.a_str = data['str']
        elseif mod == "MG.char.vitals" then
            M.stats.lp = data['hp']
            M.stats.kp = data['sp']
        elseif mod == "comm.channel" then

            -- Workaround. To be removed.
            if type(data) == "number" then
                return
            end

            print(colors.Blue .. string.sub(data['msg'], 1, -2) .. colors.Off)
        elseif mod == "MG.room.info" then
            if M.mapper.mode == "off" then
                return
            end

            local oldhash = map.room().getUserdata("hash")
            local uptodate = false

            if oldhash == "nohash" then
                mapper.V()
                return
            end

            if oldhash ~= nil and type(oldhash) ~= "table" then
                oldhash = {oldhash}
            end

            if oldhash ~= nil then
                for _,v in ipairs(oldhash) do
                    if v == data['id'] then
                        uptodate = true
                        break
                    end
                end
            end

            if M.mapper.mode == "updatehash" then
                if oldhash ~= nil and uptodate == false then
                    info(string.format("Fuege neuen Hash hinzu: %s.", data['id']))
                    table.insert(oldhash, data['id'])
                    map.room().setUserdata("hash", oldhash)
                elseif oldhash == nil then
                    map.room().setUserdata("hash", data['id'])
                    info(string.format("Hash gesetzt: '%s'", data['id']))
                end
            elseif oldhash ~= nil and uptodate == false then
                local flyto = map.room(data['id'], "hash")
                if flyto == nil then
                    M.mapper.currentUnknownHash = data['id']
                    info(string.format("Hash-Konflikt! Raum %s nicht gefunden.", data['id']))
                else
                    flyto.goto()
                    info(string.format("Hash-Konflikt! Fliege zu %s.", data['id']))
                end
                M.mapper.setMode("fixed")
            end
            mapper.V()
        end

        M.onReport()
    end)

    telnet.negDo(201)
    telnet.gmcpObject("Core.Hello", {client="mudblood", version="0.1"})
    telnet.gmcpArray("Core.Supports.Set", {"MG.char 1", "comm.channel 1", "MG.room 1"})
    telnet.gmcpValue("Core.Debug", 1)

    M.gmcp.active = true
end

--}}}

------------------------------------------------------------------------------
-------------------- FARBEN --------------------------------------------------
------------------------------------------------------------------------------

--{{{
M.base.talkTriggers = triggers.TriggerList.create()

local function mgTalkTrigger(startpattern, color)
    return triggers.Trigger.create(
        startpattern,
        function (self, l)
            if type(l) ~= "string" then return nil, false, false end

            if self.active == true then
                if string.match(l, "^ ") then
                    return color .. l .. colors.Off, true, false
                end
            end

            if string.match(l, startpattern) then
                self.active = true
                return color .. l .. colors.Off, true, false
            end

            self.active = false
        end)
end

-- Ebenen
M.base.talkTriggers:add(mgTalkTrigger("^%[[^%]]+:[^%]]+%]", colors.Blue))

-- Teile mit
M.base.talkTriggers:add(mgTalkTrigger("^%w+ teilt Dir mit: ", colors.Blue))
M.base.talkTriggers:add(mgTalkTrigger("^Dein Freund %w+ teilt Dir mit: ", colors.Blue))
M.base.talkTriggers:add(mgTalkTrigger("^Deine Freundin %w+ teilt Dir mit: ", colors.Blue))
M.base.talkTriggers:add(mgTalkTrigger("^.* aus der Ferne", colors.Blue))

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
--}}}

------------------------------------------------------------------------------
-------------------- MAPPING -------------------------------------------------
------------------------------------------------------------------------------

--{{{
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
--}}}

------------------------------------------------------------------------------
-------------------- MAPPER --------------------------------------------------
------------------------------------------------------------------------------

--{{{
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

M.mapper.overlay = {'base'}
M.mapper.layer = 'base'

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

    nmap(M.keyprefix .. "f", function () prompt("fly: ", M.mapper.fly) end)
    nmap(M.keyprefix .. "w", function () prompt("walk: ", M.mapper.walk) end)
    nmap(M.keyprefix .. "<TAB>b", M.mapper.walkBack)

    nmap(M.keyprefix .. "<TAB>d", function () prompt('walklevel: ', function (l)
        M.mapper.walklevel = tonumber(l)
        map.invalidateWeightCache()
    end) end)

    nmap(M.keyprefix .. "<TAB>mf", function () M.mapper.setMode("fixed") end)
    nmap(M.keyprefix .. "<TAB>ma", function () M.mapper.setMode("auto") end)
    nmap(M.keyprefix .. "<TAB>mn", function () M.mapper.setMode("node") end)
    nmap(M.keyprefix .. "<TAB>mo", function () M.mapper.setMode("off") end)
    nmap(M.keyprefix .. "<TAB>mm", function () M.mapper.setMode("move") end)
    nmap(M.keyprefix .. "<TAB>mu", function () M.mapper.setMode("updatehash") end)

    if M.mm then
        nmap(M.keyprefix .. "<TAB><TAB>", M.mapper.printRoomInfo)
    else
        nmap(M.keyprefix .. "<TAB><TAB>", function () screen.windowVisible('map', (not screen.windowVisible('map'))) end)
    end

    nmap(M.keyprefix .. "<TAB>n", function ()
        if map.room().getUserdata("notes") == nil then
            editor("", function (d) map.room().setUserdata("notes", d) end)
        else
            editor(map.room().getUserdata("notes"), function (d) map.room().setUserdata("notes", d) end)
        end
    end)
end

function M.mapper.setMode(m)
    M.mapper.mode = m
    info("Mapper modus: " .. m)
    M.base.status.update()
end

M.mapper.walkTrigger = triggers.line_func("mapper", function (l)
    if M.mapper.mode == "off" or M.mapper.mode == "node" then
        return
    end

    local found = false
    for k,v in pairs(map.room().overlay(M.mapper.overlay)) do
        if l == k then
            v.follow().goto()
            found = true
            break
        end
    end

    if found and M.gmcp.active then
        mapper.P()
    end

    if found == false and M.mapper.mode == "auto" and M.mapper.opposites[l] ~= nil then
        local n = map.room().findNeighbor(M.mapper.overlay, l)
        if n then
            map.room().connect('base', n, l, M.mapper.opposites[l])
            n.goto()
            info("mapper: Zyklus gefunden. Neue Kante gebaut.")
        else
            local newroom = map.addRoom()
            map.room().connect('base', newroom, l, M.mapper.opposites[l])
            newroom.goto()
            info("mapper: Neuen Raum gebaut.")
        end
    end

    if M.mapper.mode == "move" then
        return false
    end
end)

function M.mapper.costFunction(r, e)
    if M.seer ~= true and string.match(e.name, "^t ") then
        return -1
    end

    if e.getUserdata('level') and e.getUserdata('level') >= M.mapper.walklevel then
        return -1
    else
        return e.weight
    end
end

function M.mapper.toPara(n)
    if n == 0 then
        M.mapper.overlay = {'base'}
        M.mapper.layer = 'base'
    elseif n == 1 then
        M.mapper.overlay = {'base', 'p1'}
        M.mapper.layer = 'p1'
    elseif n == 2 then
        M.mapper.overlay = {'base', 'p2'}
        M.mapper.layer = 'p2'
    end
    map.renderOverlay = M.mapper.overlay
end

function M.mapper.addPara1Room(room)
    newroom = map.addRoom()

    for direction, edge in pairs(room.overlay({'base', 'p1'})) do
        print(direction)
        print(#room.opposites({'base', 'p1'}, direction))
        for _,v in ipairs(room.opposites({'base', 'p1'}, direction)) do
            r = v[1]
            e = v[2]

            newroom.connect('base', r, edge.name)
            if edge.layer == 'p1' then
                r.disconnect('base', e.name)
                r.connect('base', newroom, e.name)
            else
                r.connect('p1', newroom, e.name)
            end
        end
    end

    newroom.setUserdata("para", 1)

    return newroom
end

function M.mapper.fly(r)
    target = map.room(r, "tag")
    if target == nil and tonumber(r) ~= nil then
        target = map.room(tonumber(r))
    end
    if target == nil then
        error(string.format("Ziel '%s' nicht gefunden .", tostring(r)))
    end

    target.goto()
    info("Flug erfolgreich.")
end

function M.mapper.walk(r)
    if M.mapper.mode == "off" then
        info("mapper: Kann nicht laufen, Mapper ist aus.")
    else
        target = map.room(r, "tag")
        if target == nil and tonumber(r) ~= nil then
            target = map.room(tonumber(r))
        end
        if target == nil then
            error(string.format("Ziel '%s' nicht gefunden .", tostring(r)))
        end

        if M.mapper.mode == "node" then
            M.mapper.mode = "fixed"
            M.mapper.lastroom = map.room()
            mapper.walk(target, M.mapper.overlay, M.mapper.costFunction)
            M.mapper.mode = "node"
        else
            M.mapper.lastroom = map.room()
            mapper.walk(target, M.mapper.overlay, M.mapper.costFunction)
        end
    end
end

function M.mapper.walkBack()
    local oldlast = map.room()
    M.mapper.walk(M.mapper.lastroom.id)
    M.mapper.lastroom = oldlast
end

function M.mapper.printRoomInfo()
    local edges = map.room().overlay(M.mapper.overlay)
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
    local edges = map.room().overlay(M.mapper.overlay)
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
--}}}

------------------------------------------------------------------------------
-------------------- TEAMKAMPF -----------------------------------------------
------------------------------------------------------------------------------

--{{{
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

M.team.sendTriggers:add(triggers.gsub("^g$", function ()
    M.team.team = {}
    tlRecvVolatile:add(triggers.gsub("^[ %*] (%w+)", function (n)
        if n == "Name" or n == "Tutszt" then
            return
        end
        M.team.team[n] = false
    end))
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
end))
--}}}

------------------------------------------------------------------------------
-------------------- HORDE ---------------------------------------------------
------------------------------------------------------------------------------

--{{{
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
    for k,v in pairs(map.room().overlay(M.mapper.overlay)) do
        if l == k then
            if honda_follow then
                honda_rpc.send(k)
            end
        end
    end
end))
--}}}

------------------------------------------------------------------------------
-------------------- TANJIAN -------------------------------------------------
------------------------------------------------------------------------------

--{{{
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
    nmap('<F4>', M.tanjian.spells.clanspell)
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
        M.base.status.report = string.format("%d / %d | %d / %d | v:%d (%s) | g:%d/%d | %s%s%s%s%s%s%s | %s | %s",
                    M.stats.lp, M.stats.lp_max, M.stats.kp, M.stats.kp_max, M.stats.vorsicht, M.stats.fluchtrichtung,
                    M.stats.gift, M.stats.gift_max,
                    M.stats.blind == 1 and "B" or "",
                    M.stats.taub == 1 and "T" or "",
                    M.stats.frosch == 1 and "F" or "",
                    M.tanjian.stats.hayai == 1 and "HA" or "",
                    M.tanjian.stats.tegatana == 1 and "TE" or (M.tanjian.stats.tegatana == 2 and "OM" or ""),
                    M.tanjian.stats.kokoro == 1 and "KO" or "  ",
                    M.tanjian.stats.meditation == 1 and "M" or (M.tanjian.stats.meditation == 2 and "m" or ""),
                    M.tanjian.stats.akshara == 1 and "ja" or (M.tanjian.stats.akshara == 2 and "busy" or "nein"),
                    M.stats.gesinnung)

        M.base.status.update()
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
    M.base.spell("akshara", 2)
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

-- Clanspells

function M.tanjian.spells.clanspell()
    M.base.spell("kageodori %f", 2)
end
--}}}

------------------------------------------------------------------------------
-------------------- KLERIKER ------------------------------------------------
------------------------------------------------------------------------------

--{{{
M.klerus = {}

M.klerus.spells = {}

function M.klerus.setup()
    nmap("<LT>ur", function () M.klerus.spells.elementarschild("erde") end)
    nmap("<LT>uf", function () M.klerus.spells.elementarschild("feuer") end)
    nmap("<LT>ue", function () M.klerus.spells.elementarschild("eis") end)
    nmap("<LT>uw", function () M.klerus.spells.elementarschild("wasser") end)
    nmap("<LT>ul", function () M.klerus.spells.elementarschild("luft") end)
    nmap("<LT>us", function () M.klerus.spells.elementarschild("saeure") end)

    nmap("<LT>ir", function () M.klerus.spells.elementarsphaere("erde") end)
    nmap("<LT>if", function () M.klerus.spells.elementarsphaere("feuer") end)
    nmap("<LT>ie", function () M.klerus.spells.elementarsphaere("eis") end)
    nmap("<LT>iw", function () M.klerus.spells.elementarsphaere("wasser") end)
    nmap("<LT>il", function () M.klerus.spells.elementarsphaere("luft") end)
    nmap("<LT>is", function () M.klerus.spells.elementarsphaere("saeure") end)

    nmap("<LT>o", M.klerus.spells.frieden)
    nmap("<LT>p", M.klerus.spells.spaltung)
    
    nmap("<LT>y", M.klerus.spells.heiligenschein)
    nmap("<LT>h", M.klerus.spells.weihe)

    nmap("<LT>j", M.klerus.spells.blitz)
    nmap("<LT>k", M.klerus.spells.erloese)
    nmap("<LT>l", M.klerus.spells.laeutere)
    nmap("<LT>;", M.klerus.spells.goetterzorn)
    nmap("<LT>b", M.klerus.spells.donner)

    nmap("<LT>n", function () M.klerus.spells.heile("team") end)
    nmap("<LT>m", function () M.klerus.spells.segne("team") end)
    nmap("<LT>,", M.klerus.spells.goettermacht)
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

function M.klerus.spells.laeutere()
    M.base.spell("laeutere %f")
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

function M.klerus.spells.heile(wen)
    M.base.spell("heile " .. wen)
end

function M.klerus.spells.segne(wen)
    M.base.spell("segne " .. wen, 2, tru)
end

function M.klerus.spells.spaltung()
    M.base.spell("spaltung")
end
--}}}

------------------------------------------------------------------------------
-------------------- KAEMPFER ------------------------------------------------
------------------------------------------------------------------------------

--{{{
M.kaempfer = {}
M.kaempfer.spells = {}

function M.kaempfer.setup()
    nmap("<LT>", M.kaempfer.combo)
    nmap("<F1>", M.kaempfer.spells.fokus)
    nmap("<F5>", M.kaempfer.spells.schildparade)

    nmap("<F12>", function ()
        prompt("waffenwurf:", function (w)
            M.kaempfer.waffenwurf_waffe = w
        end)
    end)

    tlSend:add(M.kaempfer.triggerZueck)
end

function M.kaempfer.combo()
    prompt("COMBO: ", function (p)
        for i=1,#p do
            local c = p:sub(i,i)
            if c == "j" then
                M.kaempfer.spells.finte()
            elseif c == "k" then
                M.kaempfer.spells.schildstoss()
            elseif c == "l" then
                M.kaempfer.spells.kampftritt()
            elseif c == "u" then
                M.kaempfer.spells.waffenwurf()
            else
                info("Unbekannte Technik: " .. c)
            end
        end
    end)
end

M.kaempfer.waffenwurf_waffe = nil

M.kaempfer.triggerZueck = triggers.gsub("zueck (%w+)", function (w)
    M.kaempfer.waffe = w
end)

-- Spells

function M.kaempfer.spells.kampftritt()
    M.base.spell("kampftritt %f")
end

function M.kaempfer.spells.schildstoss()
    M.base.spell("schildstoss %f")
end

function M.kaempfer.spells.schildparade()
    M.base.spell("schildparade")
end

function M.kaempfer.spells.fokus()
    M.base.spell("fokus %f")
end

function M.kaempfer.spells.finte()
    M.base.spell("finte")
end

function M.kaempfer.spells.waffenwurf()
    if M.kaempfer.waffenwurf_waffe ~= nil then
        directSend("zueck " .. M.kaempfer.waffenwurf_waffe)
        M.base.spell("waffenwurf %f")
        directSend("zueck " .. M.kaempfer.waffe)
    else
        M.base.spell("waffenwurf %f")
    end
end
--}}}


return M
