--- Mudblood map functions.
-- @module map

if false then
    --- Load a map from a file.
    -- @tparam string filename The map file to load
    -- @tparam string mode The locking mode for the map. "r" (default) opens the map read-only. "w"
    --                     opens the map for writing. Only one instance of mudblood can open a map
    --                     file in "w" mode.
    function load(filename, mode) end

    --- Get a room by tag or id.
    -- @param id A room id or room tag.
    -- @treturn map.Room The room object or nil if the room was not found.
    function room(id) end

    --- Create a new room.
    -- The new room can then be connected to another room.
    -- @treturn map.Room The newly created room.
    function addRoom() end
end

