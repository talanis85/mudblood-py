local M = {}

require "table"

local events = {
    input = {},
    line = {},
    connect = {},
    heartbeat = {},
    room = {},
    telneg = {}
}

function M.register(name, fun)
    table.insert(events[name], fun)
end

function M.call(name, ...)
    local ret = nil
    for k,v in ipairs(events[name]) do
        if type(arg) == "table" then
            ret = v(unpack(arg))
        else
            ret = v(arg)
        end
    end
    return ret
end

return M
