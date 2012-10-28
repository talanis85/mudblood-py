--- Helper functions for the mapper.
-- @module mapper
-- @alias M
local M = {}

require "coroutine"

--- Current braveness.
-- @see core.map.walk
M.braveness = 9

local last_room = nil

function string:split(sep)
    ret = {}
    for token in string.gmatch(self, "[^" .. sep .. "]+") do
        table.insert(ret, token)
    end
    return ret
end

--function M.opposite(o)
--    local sp = o:split(",")
--    if #sp == 2 then
--        map.room():edges()[sp[1]]:rename(sp[2])
--    end
--end

--- String to send before starting a walk.
M.pre_walk = "ultrakurz\n"

--- String to send after finishing a walk.
M.post_walk = "lang\nschau\n"

--- Walk to a room
-- Uses the current braveness setting to walk to the specified room.
-- @param room A room id (number) or a room tag (string).
function M.walk(room)
    map.room(room):walk(M.braveness, M.walker)
end

function M.walker(p)
    last_room = map.room()

    send(M.pre_walk)
    for i=1,#p do
        send(p[i] .. "\n")
        if coroutine.yield() == true then
            break
        end
    end
    send(M.post_walk)
end

--function addportal(n, name)
--    pr = map.room("portal")
--
--    map.room():tag("portal." .. name)
--    pr:connect(map.room(), "t " .. n, "")
--    map.room():vconnect(pr)
--
--    print("Portal " .. n .. " (" .. name .. ") added.")
--end

return M
