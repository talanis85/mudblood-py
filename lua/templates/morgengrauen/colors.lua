local triggers = require "triggers"
local colors = require "colors"

-- Ebenen
triggers.user:add(triggers.color_line("^%[[^%]]+:[^%]]+%]", colors.Blue))

-- Teile mit
triggers.user:add(triggers.color_line("^%w+ teilt Dir mit: ", colors.Blue))
triggers.user:add(triggers.color_line("^Dein Freund %w+ teilt Dir mit: ", colors.Blue))
triggers.user:add(triggers.color_line("^Deine Freundin %w+ teilt Dir mit: ", colors.Blue))
triggers.user:add(triggers.color_line("^.* aus der Ferne", colors.Blue))

-- Kampf
triggers.user:add(triggers.line_func("Attack", function (l)
    local attack = {
        {"verfehlst", 0, 0},
        {"kitzelst .+ am Bauch", 1, 1},
        {"kratzt", 2, 3},
        {"triffst .+ sehr hart", 11, 20},
        {"triffst .+ hart", 6, 10},
        {"triffst", 4, 5},
        {"schlaegst .+ mit dem Krachen brechender Knochen", 21, 30},
        {"zerschmetterst .+ in kleine Stueckchen", 31, 50},
        {"schlaegst .+ zu Brei", 51, 75},
        {"pulverisierst .+", 76, 100},
        {"zerstaeubst .+", 101, 150},
        {"atomisierst .+", 151, 200},
        {"vernichtest .+", 201, 300},
    }

    for k,v in ipairs(attack) do
        if string.find(l, "^  Du " .. v[1]) then
            return colors.Green .. l .. " (" .. (v[2] == v[3] and v[2] or v[2] .. "-" .. v[3]) .. ")" .. colors.Off, true, false
        end
    end

    local defense = {
        {"verfehlt Dich", 0, 0},
        {"kitzelt Dich am Bauch", 1, 1},
        {"kratzt Dich", 2, 3},
        {"trifft Dich sehr hart", 11, 20},
        {"trifft Dich hart", 6, 10},
        {"trifft Dich", 4, 5},
        {"schlaegt Dich mit dem Krachen brechender Knochen", 21, 30},
        {"zerschmettert Dich in kleine Stueckchen", 31, 50},
        {"schlaegt Dich zu Brei", 51, 75},
        {"pulverisiert Dich", 76, 100},
        {"zerstaeubt Dich", 101, 150},
        {"atomisiert Dich", 151, 200},
        {"vernichtet Dich", 201, 300},
    }

    for k,v in ipairs(defense) do
        if string.find(l, "^  .+ " .. v[1]) then
            return colors.Red .. l .. " (" .. (v[2] == v[3] and v[2] or v[2] .. "-" .. v[3]) .. ")" .. colors.Off, true, false
        end
    end

    return nil, false, false
end))
