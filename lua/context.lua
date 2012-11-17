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

function M.currentName()
    return context
end

function M.get(ctx)
    if ctx == nil then
        return c_global
    end

    if ctx == "global" then
        return c_global
    elseif ctx == "room" then
        return c_room
    end
end

function M.reset(ctx)
    if ctx == nil then
        c_global = makecontext()
    elseif ctx == "global" then
        c_global = makecontext()
    elseif ctx == "room" then
        c_room = makecontext()
    end
end

events.register("line", function (line)
    local l = line
    if l == "" then
        return " "
    end

    local cr = coroutine.create(function ()
        local gret = nil
        local ret
        local line = l

        ret = c_room.in_triggers:query(line)
        if ret ~= nil then
            line = ret
            gret = ret
        end

        ret = c_global.in_triggers:query(line)
        if ret ~= nil then
            line = ret
            gret = ret
        end

        return gret
    end)

    local e
    e, l = coroutine.resume(cr)
    if e ~= true then
        print(debug.traceback(cr, l))
        error(l)
    end
    if coroutine.status(cr) ~= "dead" then
        print('suspended')
        return ""
    end

    --l = M.get().out_triggers:query(l)

    return l
end)

events.register("input", function (line)
    local l = line

    local cr = coroutine.create(function ()
        local gret = nil
        local ret
        local line = l

        ret = c_room.in_triggers:query(line)
        if ret ~= nil then
            line = ret
            gret = ret
        end

        ret = c_global.in_triggers:query(line)
        if ret ~= nil then
            line = ret
            gret = ret
        end

        return gret
    end)

    local e
    e, l = coroutine.resume(cr)
    if e ~= true then
        print(debug.traceback(cr, l))
        error(l)
    end
    if coroutine.status(cr) ~= "dead" then
        print('suspended')
        return ""
    end
    --l = M.get().in_triggers:query(l)

    return l
end)

events.register("heartbeat", function ()
    local l
    local cr = coroutine.create(function () return M.get().timers:query(os.time()) end)
    local e
    e, l = coroutine.resume(cr)
    if e ~= true then
        error(l)
    end
end)


return M
