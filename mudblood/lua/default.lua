nmap("`", function ()
    prompt("lua: ", function (l)
        loadstring(l)()
    end)
end)

function info(str)
    print("  " .. str)
end

print(colors.Blue .. [[
    +---------------------------------------+
    |  Herzlich willkommen bei mudblood.    |
    +---------------------------------------+
]] .. colors.Off)

print([[
  (Druecke ` oder ! um in den Lua-Modus zu wechseln)
]])

local profiles = listProfiles()

if profiles == {} then
    print([[
Du hast noch keine Profile erstellt. Um ein Profil zu erstellen, lege ein Unterverzeichnis
in folgendem Verzeichnis an:
    ]])
    print(colors.Blue .. path.profileBase() .. colors.Off)
    print([[
und erstelle darin eine Datei namens 'profile.lua'.
    ]])
else
    print([[
Du hast folgende Profile definiert:
    ]])

    for _,v in ipairs(profiles) do
        print(v)
    end

    print([[

Du kannst ein Profil laden mit: [lua] ]] .. colors.Blue .. [[profile("profilname").load()]] .. colors.Off .. [[
    ]])
end

