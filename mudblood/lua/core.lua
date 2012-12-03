--- Mudblood core functions.
-- @module core

if false then
    --- Reload the currently loaded main script.
    function reload() end

    --- Connect to a host.
    -- If we are still connected, this function does nothing.
    -- @tparam string host The hostname to connect to.
    -- @tparam number port The port to be used.
    function connect(host, port) end

    --- Set the status line
    -- @tparam string status The new status line.
    function status(status) end

    --- Send data into the system.
    -- Has the same effect as writing a line of input in normal mode.
    -- @tparam string data String to send. Trailing newlines will be stripped.
    function send(data) end

    --- Send data, bypassing display and the trigger system.
    -- Like send, but nothing is displayed and no triggers are queried.
    -- @tparam string data String to send. Trailing newlines will be stripped.
    function directSend(data) end

    --- Quit mudblood.
    function quit() end

    --- Switch to prompt mode.
    -- Reads a line of input from the user.
    -- @tparam string prompt The prompt to display.
    -- @tparam function fun A callback function that will be passed the entered string as first argument.
    function prompt(prompt, fun) end

    --- Switch to visual mode.
    -- Allows the user to select one or more lines from the main buffer. The selected text will be passed to a callback.
    -- @tparam function fun The callback to use. The selected text will be passed as first argument.
    function visual(fun) end

    --- Set a configuration option.
    -- Possible keys are:
    -- - encoding: 'utf8', 'ascii', 'latin1' etc.
    -- @tparam string key The name of the option.
    -- @param value The desired new value.
    function config(key, value) end

    --- Map a key combination in normal mode.
    -- If the combination is already mapped, that mapping is overwritten.
    -- @tparam string keys The key combination to map
    -- @tparam function action A function to call when the combination is triggered.
    function nmap(keys, action) end

    --- Execute a lua script.
    -- Very much like lua's builtin dofile(), but uses path.profile() to search for the file.
    -- @tparam string filename The script file to execute.
    function load(filename) end

    --- Create an RPC server socket
    -- @tparam string type Currently, only 'unix' is supported.
    -- @param address The address to bind to. The datatype depends on the socket type.
    function rpcServer(type, address) end

    --- Connect to an RPC socket.
    -- @tparam string type Currently, only 'unix' is supported.
    -- @param address The address of the socket. The datatype depends on the socket type.
    -- @treturn RPCObject
    function rpcClient(type, address) end

    --- Spawn an editor.
    -- @tparam string content The initial contents of the editor.
    -- @treturn string The final contents of the editor.
    function editor(content) end

    --- Mark current line as a prompt.
    -- Meant to be called e.g. when an EOR or GA telneg is received.
    function markPrompt() end
end
