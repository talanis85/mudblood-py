function addTrigger(trig)
    ctxGlobal.recvTriggers:add(trig)
end

function removeTrigger(name)
    ctxGlobal.recvTriggers:remove(name)
end

function addSendTrigger(trig)
    ctxGlobal.sendTriggers:add(trig)
end

function removeSendTrigger(name)
    ctxGlobal.sendTriggers:remove(name)
end

function yield(trigs)
    triggers.yield(trigs, ctxRoom.recvTriggers)
end

function yieldInput(trigs)
    triggers.yield(trigs, ctxRoom.sendTriggers)
end

function yieldTimer(trigs)
    triggers.yield(trigs, ctxRoom.timers)
end

function roomSendBeforeExit(direction, str)
    roomOnExit(direction, function ()
        directSend(str)
    end)
end

function roomOnExit(direction, fun)
    ctxRoom.sendTriggers:add(triggers.gsub("^" .. direction .. "$", function ()
        mapper.P()
        local ret = fun()
        if ret == false then
            mapper.stop()
        else
            mapper.V()
        end

        return ret
    end))
end

function roomWaitOnExit(direction, str)
    roomOnExit(direction, function ()
        ctxRoom:wait(triggers.gsub(str))
    end)
end

