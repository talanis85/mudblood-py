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

    walk_stop = false

    if M.pre_walk then M.pre_walk() end

    for i=1,#p do
        send(p[i])
        if walk_semaphore > 0 then
            coroutine.yield()
        end
        if walk_stop == true then
            walker = nil
            walk_stop = false
            if M.post_walk then M.post_walk() end
            return
        end
    end
    walker = nil
    if M.post_walk then M.post_walk() end
end

M.pre_walk = nil
M.post_walk = nil

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
    walk_stop = true
    M.V()
end

function M.P()
    if walker then
        walk_semaphore = walk_semaphore + 1
    end
end

function M.V()
    if walker then
        if walk_semaphore > 0 then
            walk_semaphore = walk_semaphore - 1
        end

        if walk_semaphore == 0 then
            if coroutine.status(walker) ~= "normal" then
                local status, err = coroutine.resume(walker)
                if status ~= true then
                    error(err)
                end
            end
        end
    end
end

function M.walking()
    return walker ~= nil
end

return M
