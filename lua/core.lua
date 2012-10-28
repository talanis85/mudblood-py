--- Mudblood core functions.
-- @module core

if false then
    --- Reload the currently loaded main script.
    -- Note: This will not close the current connection.
    function reload() end

    --- Connect to a host.
    -- @tparam string host The hostname to connect to.
    -- @tparam number port The port to be used.
    function connect(host, port) end

    --- Set the status line
    -- @tparam string status The new status line.
    function status(status) end

    --- Send data into the system.
    -- If none of the boolean arguments are set, this has the same effect as writing a line of input in normal mode.
    -- @tparam string data String to send.
    function send(data) end

    --- Send data directly to the socket, bypassing the trigger system.
    -- @tparam string data String to send.
    function directSend(data) end

    --- Quit mudblood.
    function quit() end

    --- Switch to prompt mode.
    -- Reads a line of input from the user.
    -- @tparam string prompt The prompt to display.
    -- @tparam function fun A callback function that will be passed the entered string as first argument.
    function prompt(prompt, fun) end

    --- Switch to visual mode
    -- Allows the user to select one or more lines from the main buffer. The selected text will be passed to a callback.
    -- @tparam function fun The callback to use. The selected text will be passed as first argument.
    function visual(fun) end

    --- Set a configuration option.
    -- Possible keys are:
    -- prompt (string) - The game's prompt (for prompt detection),
    -- roomscripts (boolean) - Whether or not to use room-specific scripts,
    -- fifo (string) - The path of a FIFO to use for external input,
    -- @tparam string key The name of the option.
    -- @param value The desired new value.
    function config(key, value) end
end

-- ADDITIONAL FUNCTIONS

function sendln(l)
    if l then
        send(l .. "\n")
    end
end
