function addTrigger(trig, ctx)
    ctxGlobal.recvTriggers:add(trig)
end

function removeTrigger(name, ctx)
    context.get(ctx).out_triggers:remove(name)
end

function addInputTrigger(trig, ctx)
    context.get(ctx).in_triggers:add(trig)
end

function removeInputTrigger(name, ctx)
    context.get(ctx).in_triggers:remove(name)
end

function yield(trigs, ctx)
    triggers.yield(trigs, context.get(ctx).out_triggers)
end

function yieldInput(trigs, ctx)
    triggers.yield(trigs, context.get(ctx).in_triggers)
end

function yieldTimer(trigs, ctx)
    triggers.yield(trigs, context.get(ctx).timers)
end

