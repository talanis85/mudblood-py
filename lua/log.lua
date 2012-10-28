--- Logging your game session to a file.
-- @module log
-- @alias M
local M = {}

require "io"

--- Logging trigger.
-- A special trigger that writes every line to a file. You should add this to you trigger
-- list as early as possible.
-- @tparam string file The name of your logfile.
-- @treturn trigger.Trigger
function M.logger(file)
    local logfd = assert(io.open(file, "a"))

    return triggers.line_func("Logger", function (l)
        if l == "" then
            return nil
        end

        if logfd ~= nil then
            logfd:write(l .. "\n")
            logfd:flush()
        end

        return nil
    end)
end

return M
