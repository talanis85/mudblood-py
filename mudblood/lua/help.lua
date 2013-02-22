require "io"
require "table"

local function ask(question)
    local ret

    print(" " .. question)

    _, ret = ctxGlobal:waitSend({triggers.any("input prompt")})

    return ret
end

local function more()
    ask("ENTER to continue")
end

function help(topic)
    fd = io.open(path.library() .. "/help/" .. topic)
    if fd == nil then
        print("-- There is no help for '" .. topic .. "'")
        return
    end

    print(fd:read("*all"))
end

