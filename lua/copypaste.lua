local M = {}

require "io"
require "os"

function M.follow_link(l)
    for link in string.gmatch(l, "http://[^ \n]+") do
        exec("uzbl " .. link, nil)
    end
end

function M.paste()
    local clip = exec("xclip -o", nil)
    local clips = clip:split("\n")
    send(":schliesst die Augen und konzentriert sich. Dann beginnt er wie in Trance zu sprechen.\n")
    for k,v in ipairs(clips) do
        send("sag " .. v .. "\n")
    end
end

function M.exec(cmd, stdin)
    if stdin == nil then
        stdin = ""
    end

    tmpout = os.tmpname()
    tmpin = os.tmpname()

    fd = assert(io.open(tmpin, "w"))
    fd:write(stdin)
    fd:close()

    ret = os.execute(cmd .. " <" .. tmpin .. " >" .. tmpout)
    if ret ~= true then
        print("Error executing " .. cmd)
    else
        fd = assert(io.open(tmpout, "r"))
        out = fd:read("*all")
        fd:close()
    end
    os.remove(tmpin)
    os.remove(tmpout)

    return out
end

return M
