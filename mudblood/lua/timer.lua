require "os"
require "table"

local M = {}

local timers = {}

function M.setup()
    event_heartbeat = function ()
        local cur = os.time()
        for i,t in ipairs(timers) do
            if cur > t.endtime then
                t.fun()
                table.remove(timers, i)
            end
        end
    end
end

function M.oneshot(length, fun)
    table.insert(timers, { endtime = os.time() + length, fun = fun })
end

return M

