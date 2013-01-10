--- Mudblood trigger system.
-- Triggers are a way to react to incoming data from the game. Every time mudblood
-- receives a complete line, it feeds that line into the trigger system. The trigger
-- then either ignores that line or reacts by performing an action and/or modifying
-- the line. You can use TriggerLists to organize triggers hierarchically (a
-- TriggerList is a trigger that queries serveral sub-triggers). TriggerList inherits
-- the Trigger interface, so everywhere when you use a Trigger, you can use a TriggerList, too.
-- Note that triggers and timers share the same interface. A timer is nothing else than a
-- trigger that ignores its line argument and instead checks the difference between its
-- creation time and the current time.
-- @module triggers
-- @alias M
local M = {}

require "table"
require "string"
require "os"
require "coroutine"

local colors = require "colors"
local mapper = require "mapper"

function string:split(sep)
    ret = {}
    for token in string.gmatch(self, "[^" .. sep .. "]+") do
        table.insert(ret, token)
    end
    return ret
end

M.Trigger = {}
M.Trigger.__index = M.Trigger

--- Create a new trigger.
-- @tparam string repr The textual representation of the trigger
-- @tparam function fun The trigger's query function
-- @treturn Trigger The new trigger
-- @function Trigger.create
function M.Trigger.create(repr, fun)
    local trig = {}

    setmetatable(trig, M.Trigger)

    trig.query = fun
    trig.repr = function () return repr end

    return trig
end

--- Trigger interface.
-- @type Trigger
    
--- Query a trigger.
-- This is the trigger's main function. When the trigger is queried, its query function is
-- called with the triggering line or the current timestamp as argument.
-- @param arg If the trigger is queried for an incoming line, this argument
--            is a string containing that line. If the trigger is queried as
--            a timer, the argument is the current timestamp as a number.
-- @treturn string The modified line or nil. Has no effect, when queried for a
--                 timestamp.
-- @treturn boolean true if the trigger did actually fire
-- @treturn boolean true if the trigger wants to be removed from its parent list
function M.Trigger:query(arg)
end

--- Get a textual description of the trigger.
-- This is used in TriggerList:show()
-- @treturn string A string describing the trigger
function M.Trigger:repr()
end

--- Extend a trigger.
-- If you want a trigger to perform additional action when it fires, you can add
-- a function (henceforth referred to as "trigger fragment") to it.
-- That function will be executed after the trigger's original
-- function if and only if that trigger returned true as its second return value
-- (i.e. it signaled that it fired)
-- @tparam function fun A trigger fragment (see Trigger:fun())
-- @treturn Trigger The new trigger with the added trigger fragment
-- @see Trigger:query
function M.Trigger:__add(fun)
    assert(type(fun) == "function")
    local oldfun = self.query
    return M.Trigger.create(self:repr() .. " +", function (self2, args)
            local ret, fire, rem = oldfun(self2, args)
            local ret2 = nil
            local rem2 = false
            if fire == true then
                ret2, rem2 = fun(self2, args)
            end
            if ret2 == nil then ret2 = ret end
            if rem2 ~= true then rem2 = rem end
            return ret2, fire, rem2
        end
    )
end

--- @section end

M.TriggerList = {}
M.TriggerList.__index = M.TriggerList

--- Creates a new trigger list.
-- A trigger list is composed of multiple triggers that are executed in order. If one trigger
-- modifies the line (i.e. returns a string as its first return value), that new line will
-- be passed to all following triggers instead of the original.
-- @tparam boolean one_shot If true, the trigger list will request to have itself removed as soon
--                 as one of its sub-triggers requests removal.
-- @treturn TriggerList A new TriggerList
-- @function TriggerList.create
function M.TriggerList.create(one_shot)
    local tlist = {}

    setmetatable(tlist, M.TriggerList)
    tlist.list = {}
    tlist.one_shot = one_shot

    return tlist
end

--- TriggerList interface.
-- @type TriggerList

--- Add a sub-trigger.
-- @tparam Trigger trigger The trigger to be added.
-- @tparam string name (Optional) A name that uniquely identifies this trigger in the list
-- @tparam number priority (Optional) The lower the priority, the earlier the trigger gets
--                         inserted into the list.
-- @treturn Trigger The added trigger.
function M.TriggerList:add(trigger, name, priority)
    if priority == nil then
        priority = 0
    end

    local table_pos = 1
    for i,v in ipairs(self.list) do
        if name ~= nil and name == v.name then
            error("A trigger with name '" .. name .. "' already exists in this list.")
        end
        if priority <= v.priority then
            table_pos = i+1
            break
        end
    end

    trigger.name = name
    trigger.priority = priority

    table.insert(self.list, table_pos, trigger)

    return trigger
end

--- Remove a sub-trigger.
-- @param index The index or name of the trigger to remove.
function M.TriggerList:remove(index)
    if type(index) == "string" then
        for k,v in ipairs(self.list) do
            if v.name == index then
                index = k
                break
            end
        end
    end
    if type(index) == "string" then
        error("Trigger '" .. index .. "' not found in list.")
    end
    table.remove(self.list, index)
end

--- Remove all sub-triggers.
function M.TriggerList:clear()
    for i=1,#self.list do
        table.remove(self.list, 1)
    end
end

--- Print the trigger list.
function M.TriggerList:show()
    print(self:repr())
end

--- Query all sub-triggers in their list order.
-- @tparam string l The line.
-- @treturn string The modified line or nil.
function M.TriggerList:query(l)
    local changed = false
    local grem = nil
    local gfire = false
    local to_remove = {}
    local copy = {}
    for k,v in ipairs(self.list) do
        copy[k] = v
    end
    for i=1,#copy do
        local ret = nil
        local rem = false
        local fire = false
        ret, fire, rem = copy[i]:query(l)
        if fire then
            gfire = true
        end
        if rem == true then
            for j, t2 in ipairs(self.list) do
                if copy[i] == t2 then
                    table.remove(self.list, j)
                    break
                end
            end
            grem = true
        end
        if ret ~= nil then
            l = ret
            changed = true
            if l == false then
                break
            end
        end
    end

    if changed == false then
        l = nil
    end

    if self.one_shot == true and grem == true then
        return l, gfire, true
    else
        return l, gfire, false
    end
end

function M.queryListsAndSend(lists, l)
    local gr2 = false
    local gr3 = false
    local changed = false
    mapper.P()
    for _, tlist in ipairs(lists) do
        local r1,r2,r3 = tlist:query(l)
        if r1 == false then
            mapper.V()
            return true
        elseif r1 ~= nil then
            l = r1
            changed = true
        end
        if r2 then gr2 = true end
        if r3 then gr3 = true end
    end
    directSend(l)
    mapper.V()
    return true
end

function M.queryListsAndEcho(lists, al)
    local l = tostring(al)
    local gr2 = false
    local gr3 = false
    local changed = false
    mapper.P()
    for _, tlist in ipairs(lists) do
        local r1,r2,r3 = tlist:query(l)
        if r1 == false then
            mapper.V()
            return true
        elseif r1 ~= nil then
            l = r1
            changed = true
        end
        if r2 then gr2 = true end
        if r3 then gr3 = true end
    end
    if changed then
        print(l)
    else
        print(al)
    end
    mapper.V()
    return true
end

--- String representation of the TriggerList.
-- Returns a textual description of the TriggerList. The list is traversed
-- recursively and the whole tree of trigger lists is returned.
-- @treturn string The representation of the TriggerList
function M.TriggerList:repr()
    local ret = ""
    for i,t in ipairs(self.list) do
        local rep

        if t.list ~= nil then
            -- This is a trigger list -> indent its representation
            rep = "TriggerList:"
            local replines = string.split(t:repr(), "\n")
            for k,v in ipairs(replines) do
                rep = rep .. "\n\t" .. v
            end
        else
            rep = t:repr()
        end

        if t.name then
            ret = ret .. i .. " (" .. t.name .. "): " .. rep .. "\n"
        else
            ret = ret .. i .. ": " .. rep .. "\n"
        end
    end
    return ret
end

--- @section end

--- Pre-defined triggers
-- @section triggers

--- Sends a response when a certain pattern is found.
-- @tparam string pattern The pattern to search for
-- @tparam string response What so send when the string is found
-- @treturn Trigger
function M.simple(pattern, response)
    return M.Trigger.create(
        pattern .. " -> " .. response,
        function (self, l)
            if type(l) ~= "string" then return nil, false, false end

            if string.find(l, pattern) then
                send(response .. "\n")
                return nil, true, false
            end
            return nil, false, false
        end
    )
end

--- Color the line when it contains a certain pattern.
-- @tparam string pattern The pattern to search for
-- @tparam string color A color
-- @treturn Trigger
function M.color_line(pattern, color)
    return M.Trigger.create(
        pattern .. " => Colorize",
        function (self, l)
            if type(l) ~= "string" then return nil, false, false end

            if string.find(l, pattern) then
                return color .. l .. colors.Off, true, false
            end
            return nil, false, false
        end
    )
end

--- Sophisticated pattern matching.
-- Uses Lua's gsub function to match against a pattern and if that pattern
-- is found, call the given function with the pattern's groups as arguments.
-- @param pattern The pattern to match. If the pattern contains newlines (\n), it
--                is interpreted as a multi-line pattern. If pattern is a table of strings,
--                these are intepreted as alternative patterns.
-- @tparam function fun The function to call if the pattern is found. That function can
--                      return up to two values: The first value is the modified line (or
--                      nil if it should not be modified) and the second value is a boolean
--                      value denoting if the trigger wants to be removed from its parent list.
-- @treturn Trigger
-- @see string.gsub
function M.gsub(pattern, fun)
    local curl = 1
    local ret = {}

    if type(pattern) == type({}) then
        return M.Trigger.create(pattern[1] .. " or something else", function (self, l)
                if type(l) ~= "string" then return nil, false, false end

                local r1 = nil
                local r2 = false 
                local r3 = false
                for _,v in ipairs(pattern) do
                    local findret = {string.find(l, v)}
                    if findret[1] ~= nil then
                        if fun then
                            local args = {}
                            for i=3,#findret do
                                table.insert(args, findret[i])
                            end
                            r1, r3 = fun(unpack(args))
                        end
                        r2 = true
                    end
                    --string.gsub(l, v, function (...)
                    --    if fun then
                    --        r1, r3 = fun(unpack(arg))
                    --    end
                    --    r2 = true
                    --end)
                    if r2 then
                        break
                    end
                end
                return r1, r2, r3
            end)
    else
        pattern = pattern:split("\n")
        if type(pattern) == type("") then
            pattern = { pattern }
        end
        return M.Trigger.create(pattern[1] .. "...", function (self, l)
                if type(l) ~= "string" then return nil, false, false end

                local r1 = nil
                local r2 = false
                local r3 = false

                local findret = {string.find(l, pattern[curl])}
                if findret[1] ~= nil then
                    for i=3,#findret do
                        table.insert(ret, findret[i])
                    end
                    if curl == #pattern then
                        curl = 1
                        if fun then
                            r1, r3 = fun(unpack(ret))
                        end
                        ret = {}
                        r2 = true
                    else
                        curl = curl + 1
                    end
                else
                    curl = 1
                    ret = {}
                end

                return r1, r2, r3
            end)
    end
end

--- A trigger that fires on any input
-- @tparam string desc The trigger's description
-- @treturn Trigger
function M.any(desc)
    return M.Trigger.create(
        desc,
        function (self, l)
            if type(l) ~= "string" then return nil, false, false end

            return nil, true, false
        end
    )
end

--- Call a function on every line.
-- @tparam string desc The trigger's description
-- @tparam function f The function to call
-- @treturn Trigger
function M.line_func(desc, f)
    return M.Trigger.create(
        desc,
        function (self, l)
            if type(l) ~= "string" then return nil, false, false end

            return f(l)
        end
    )
end

--- Wait for the next line.
-- A one shot trigger that will fire on the next line.
-- @tparam string desc The trigger's description
function M.one_line(desc)
    if desc == nil then desc = "one_line" end
    return M.Trigger.create(
        desc,
        function (self, l)
            if type(l) ~= "string" then return nil, false, false end
            return nil, true, true
        end
    )
end

--- Wait for a certain amount of time and then call a function.
-- @tparam string desc The trigger's description
-- @tparam number length Number of seconds to wait. Note that this is quite
--                       imprecise for now with an error of about +/- 1 second
-- @tparam function f The function to call
-- @treturn Trigger
function M.timer(desc, length, f)
    local endtime = os.time() + length
    return M.Trigger.create(desc, function (self)
            if os.time() >= endtime then
                if f then f() end
                return nil, true, true
            end
            return nil, false, false
        end)
end

--- Same as timer only that the timer is restarted every time it fires.
-- @tparam string desc The trigger's description
-- @tparam number length Number of seconds to wait.
-- @tparam function f The function to call. If f returns true then the timer is removed.
-- @treturn M.Trigger
-- @see triggers.timer
function M.repeat_timer(desc, length, f)
    local endtime = os.time() + length
    return M.Trigger.create(desc, function (self)
            if os.time() > endtime then
                if f() == true then
                    return nil, true, true
                else
                    endtime = endtime + length
                    return nil, true, false
                end
            end
            return nil, false, false
        end
    )
end

--- Trigger fragments.
-- @section fragments

--- Send a line.
-- When added to a trigger, cause that trigger to send a line after it fired.
-- @tparam string line The line to send.
-- @treturn function The trigger fragment.
-- @usage local trig = triggers.gsub("pattern") + triggers.f_sendln("found it")
function M.f_sendln(line)
    return function (self)
        send(line .. "\n")
    end
end

--- Trigger-based coroutines.
-- @section async

local function f_resume(cr, data)
    return function (self, arg)
        ret, err = coroutine.resume(cr, data, arg)
        if ret == false then
            error(err)
        end
        return nil, true
    end
end

--- Create a triggered coroutine.
-- Triggered coroutines are a convenient way to write functions that can suspend execution until
-- some trigger is fired. The concept works much like Lua coroutines. After calling triggers.coroutine(),
-- the resulting coroutine can be called with exactly the same arguments as the original function to
-- start execution of the coroutine.
-- @tparam function fun The coroutine's main function
-- @treturn function A triggered coroutine
-- @usage local example = triggers.coroutine(function (arg1, arg2)
--           send(arg1 .. "\n")
--           triggers.yield(triggers.timer("a timer", 5))
--           send(arg2 .. "\n")
--        end)
--        example("hello", "world")
-- @see coroutine.wrap()
function M.coroutine(fun)
    return function (...)
        local ret, err
        if ... and type(...) == "table" then
            ret, err = coroutine.resume(coroutine.create(fun), unpack(...))
        else
            ret, err = coroutine.resume(coroutine.create(fun), ...)
        end
        if ret == false then
            error(err)
        end
    end
end

--- Suspend execution of a coroutine.
-- Can only be called inside a triggered coroutine. The coroutine is suspended until the given trigger
-- fires. The trigger is always created as a one-shot trigger.
-- @tparam Trigger trigger The trigger to wait for.
-- @tparam TriggerList Trigger list to add the trigger to. Defaults to triggers.system.
-- @return Dunno
function M.yield(trigs, tlist)
    if trigs.query ~= nil then
        trigs = { trigs }
    end

    local trig_list = M.TriggerList.create(true)

    for k,v in ipairs(trigs) do
        trig_list:add(v + f_resume(coroutine.running(), k))
    end

    tlist:add(trig_list)
    return coroutine.yield()
end


return M
