local M = {}

local trig_in = {}
local trig_out = {}

local pause_count = 0

trig_out = triggers.system:add(triggers.TriggerList.create(false))
trig_in = triggers.input.system:add(triggers.TriggerList.create(false))

events.register("room", function ()
    trig_in:clear()
    trig_out:clear()
    pause_count = 0
end)

function M.trigger(t)
    trig_out:add(t)
end

function M.trigger_in(t)
    trig_in:add(t)
end

function M.stop()
    map.walkctl(0)
end

function M.pause()
    map.walkctl(1)
    pause_count = pause_count + 1
end

function M.continue()
    pause_count = pause_count - 1
    if pause_count <= 0 then
        map.walkctl(2)
    end
end

function M.on_exit(d, cr)
    trig_in:add(triggers.gsub("^(" .. d .. ")$", function (dir)
        M.pause()
        local acr = triggers.coroutine(function ()
            local cont, send_exit = cr(dir)
            if cont == false then
                M.stop()
            else
                M.continue()
            end
            if send_exit == false then
                return nil
            else
                send(dir .. "\n", true)
            end
        end)
        acr()
        return ""
    end))
end

--function M.try_exit(d, trig)
--    trig_in:add(triggers.gsub("^" .. d .. "$", function ()
--        if type(trig) ~= type({}) then
--            trig = { trig }
--        end
--
--        local outlist = trig_out:add(triggers.triggerlist("Try exit: " .. d, true))
--
--        for k,v in ipairs(trig) do
--            local f = function (...)
--                local ret
--                if fun[k] then
--                    ret = fun[k](unpack(arg))
--                end
--                if ret ~= false then
--                    send(d .. "\n", true, false, true)
--                    M.continue()
--                end
--                return nil, true, true
--            end
--            if type(v) == type(0) then
--                -- nothing
--            elseif type(v) == type("") then
--                outlist:add(triggers.gsub(v, f))
--            end
--        end
--
--        send(d .. "\n", true, true, false)
--        M.pause()
--
--        return "", true, false
--    end))
--end

function M.try_exit(d, trig)
    M.before_exit(d, d, trig)
end

function M.f_try_again(d)
    return function ()
        trig_out:add(triggers.timer("Try again: " .. d, 2, function ()
            send(d .. "\n", false, false, false)
        end))
        return nil, true
    end
end

function M.f_continue(d)
    return function ()
        send(d .. "\n", true, false, false)
        M.continue()
    end
end

function M.f_stop()
    return function ()
        M.stop()
    end
end

function M.before_exit(d, fun, trig)
    trig_in:add(triggers.gsub("^" .. d .. "$", function ()
        if trig ~= nil then
            if type(trig) ~= type({}) then
                trig = { trig }
            end

            local outlist = trig_out:add(triggers.TriggerList.create(true))

            for k,v in ipairs(trig) do
                outlist:add(v)
            end
        end

        if type(fun) == type("") then
            send(fun .. "\n", true, true, false)
        else
            fun(d)
        end
        if trig ~= nil then
            M.pause()
            return "", false
        end
    end))
end

--function M.before_exit(d, fun1, pat, fun2)
--    trig_in:add(triggers.gsub("^" .. d .. "$", function ()
--        if pat ~= nil then
--            if type(pat) ~= type({}) then
--                pat = { pat }
--                fun2 = { fun2 }
--            end
--
--            local outlist = trig_out:add(triggers.triggerlist("Before exit: " .. d, true))
--
--            for k,v in ipairs(pat) do
--                outlist:add(triggers.gsub(v, function (...)
--                    local ret
--                    if fun2 and fun2[k] then
--                        ret = fun2[k](unpack(arg))
--                    end
--                    if ret ~= false then
--                        send(d .. "\n", true, false, false)
--                        M.continue()
--                    end
--                    return nil, true, true
--                end))
--            end
--        end
--
--        if type(fun1) == type("") then
--            send(fun1 .. "\n", true, true, false)
--        else
--            fun1(d)
--        end
--        if pat ~= nil then
--            M.pause()
--            return "", true, false
--        end
--    end))
--end

return M

