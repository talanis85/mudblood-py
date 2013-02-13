local M = {}

require "table"

local events = {
    input = {},
    line = {},
    connect = {},
    disconnect = {},
    heartbeat = {},
    room = {},
    telneg = {},
    gmcp = {}
}

function M.register(name, fun)
    table.insert(events[name], fun)
end

function M.call(name, arg)
    local ret = nil
    for k,v in ipairs(events[name]) do
        ret = v(unpack(arg))
    end
    return ret
end

return M
