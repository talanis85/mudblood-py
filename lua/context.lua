M = {}

local context = "global"

local function makecontext()
    local ret = {}
    ret.in_triggers = triggers.TriggerList.create()
    ret.out_triggers = triggers.TriggerList.create()
    ret.timers = triggers.TriggerList.create()
    return ret
end

local c_global = makecontext()
local c_room = makecontext()

function M.switch(c)
    if c ~= "global" and c ~= "room" then
        error("Invalid context: " .. c)
    end
    context = c
end

function M.current()
    if context == "global" then
        return c_global
    elseif context == "room" then
        return c_room
    end
end

function M.get(ctx)
    if ctx == nil then
        ctx = context
    end

    if ctx == "global" then
        return c_global
    elseif ctx == "room" then
        return c_room
    end
end

events.register("line", function (line)
    l = line
    if l == "" then
        return " "
    end

    l = M.get().out_triggers:query(l)

    return l
end)

events.register("input", function (line)
    l = line

    l = M.get().in_triggers:query(l)

    return l
end)

events.register("heartbeat", function ()
    M.get().timers:query(os.time())
end)


return M
