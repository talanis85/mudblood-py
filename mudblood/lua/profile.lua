--- Profile management.
-- @module profile
-- @alias M
local M = {}

require "lfs"
require "io"
require "table"

local function ask(question)
    local ret

    print(" " .. question)

    _, ret = ctxGlobal:waitSend({triggers.any("profile wizard")})

    return ret
end

M.wizard = triggers.coroutine(function ()
    local name, template

    name = ask("Enter name of new profile:")

    print("Available templates in " .. path.library() .. "/templates are:")
    for d in lfs.dir(path.library() .. "/templates") do
        if d ~= "." and d ~= ".." then
            print(" - " .. d)
        end
    end

    template = ask("Enter name of template:")

    print("Okay, creating profile '" .. name .. "' with template '" .. template .. "'")

    M.create(name, template)

    print("Done. To load the new profile, close mudblood and re-run with:")
    print("  mudblood " .. name)
end)

function M.create(name, template)
    local ret, err

    ret, err = lfs.attributes(path.library() .. "/templates/" .. template)
    if err then
        error("Template '" .. template .. "' does not exist")
        return
    end

    ret, err = lfs.mkdir(path.profileBase() .. "/" .. name)
    if err then
        error("Could not create profile: " .. err)
        return
    end

    local fin, fout
    for d in lfs.dir(path.library() .. "/templates/" .. template) do
        if d ~= "." and d ~= ".." then
            print("Copying " .. d)
            local fin = assert(io.open(path.library() .. "/templates/" .. template .. "/" .. d, "r"))
            local fout = assert(io.open(path.profileBase() .. "/" .. name .. "/" .. d, "w"))
            fout:write(fin:read("*all"))
        end
    end
end

return M

