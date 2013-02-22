print("Hallo, willkommen bei Mudblood!")

print("Folgende Profile gibt es:")
print("--------------------------------------------")
for _,v in ipairs(listProfiles()) do
    print(v)
end

print("Lade eins mit: (lua) profile('profilname').load()")

