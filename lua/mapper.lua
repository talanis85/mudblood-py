--- Helper functions for the mapper.
-- @module mapper
-- @alias M
local M = {}

require "coroutine"

local walker = nil
local walk_semaphore = 0
local walk_stop = false

local function walk_cr(room, weightFunction)
    local p = map.room().getPath(room, weightFunction)
    local cr = coroutine.running()

    for i=1,#p do
        local dir = p[i]
        send(dir .. "\n", {continuation=cr, display=false})
        coroutine.yield()
        if walk_semaphore > 0 then
            coroutine.yield()
        end
        if walk_stop == true then
            walker = nil
            walk_stop = false
            return
        end
    end
    walker = nil
end

function M.walk(room, weightFunction)
    walker = coroutine.create(walk_cr)
    walk_semaphore = 0
    local status, err = coroutine.resume(walker, room, weightFunction)
    if status ~= true then
        error(err)
    end
end

function M.stop()
    walk_semaphore = 0
end

function M.P()
    print("mapper.P()")
    walk_semaphore = walk_semaphore + 1
end

function M.V()
    print("mapper.V()")
    if walk_semaphore > 0 then
        walk_semaphore = walk_semaphore - 1
    end

    if walk_semaphore == 0 then
        local status, err = coroutine.resume(walker)
        if status ~= true then
            error(err)
        end
    end
end

function M.walking()
    return walker ~= nil
end

return M
