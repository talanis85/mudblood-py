--- Profile management.
-- @module profile
-- @alias M
local M = {}

require "lfs"
require "io"
require "table"

M.wizard = triggers.coroutine(function ()
    local name, template

    print("Enter name of new profile:")
    name = triggers.yield(triggers.one_line(), triggers.input.system)

    print("Available templates in " .. library_path .. "/templates are:")
    for d in lfs.dir(library_path .. "/templates") do
        if d ~= "." and d ~= ".." then
            print("\t" .. d)
        end
    end

    print("Enter name of template:")
    template = triggers.yield(triggers.one_line(), triggers.input.system)

    print("Okay, creating profile '" .. name .. "' with template '" .. template .. "'")

    M.create(name, template)

    print("Done. To load the new profile, close mudblood and re-run with:")
    print("  mudblood " .. name)
end)

function M.create(name, template)
    local ret, err

    ret, err = lfs.attributes(library_path .. "/templates/" .. template)
    if err then
        error("Template '" .. template .. "' does not exist")
        return
    end

    ret, err = lfs.mkdir(name)
    if err then
        error("Could not create profile: " .. err)
        return
    end

    local fin, fout
    for d in lfs.dir(library_path .. "/templates/" .. template) do
        if d ~= "." and d ~= ".." then
            print("Copying " .. d)
            local fin = assert(io.open(library_path .. "/templates/" .. template .. "/" .. d, "r"))
            local fout = assert(io.open(name .. "/" .. d, "w"))
            fout:write(fin:read("*all"))
        end
    end
end

return M

