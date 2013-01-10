mg = require "mud.mg" 

mg.setup("abenteurer", false)

events.register("connect", function ()
    send("Name")
    send("passwort")
end)

map.load(path.profile() .. "/map")

connect("mg.mud.de", 4711)
