--- Helper functions for the mapper.
-- @module mapper
-- @alias M
local M = {}

require "coroutine"

local walker = nil
local walk_semaphore = 0

local function walk_cr(room)
    local p = map.room().getPath(room)

    for i=1,#p do
        send(p[i] .. "\n")
        if walk_semaphore > 0 then
            coroutine.yield()
        end
        if walk_semaphore == -1 then
            walker = nil
            return
        end
    end
end

function M.walk(room)
    walker = coroutine.create(walk_cr)
    walk_semaphore = 0
    coroutine.resume(walker, room)
end

function M.stop()
    if walker == nil then
        error("Not walking")
    end

    walk_semaphore = -1
end

function M.P()
    if walker == nil then
        error("Not walking")
    end

    walk_semaphore = walk_semaphore + 1
end

function M.V()
    if walker == nil then
        error("Not walking")
    end

    if walk_semaphore > 0 then
        walk_semaphore = walk_semaphore - 1
    end

    if walk_semaphore == 0 then
        coroutine.resume(walker)
    end
end

return M
