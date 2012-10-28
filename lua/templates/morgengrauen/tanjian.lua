
-- BINDINGS

nmap('<F1>', 'meditation')
nmap('<F2>', 'kokoro')
nmap('<F3>', '!spell("kami")')
nmap('<F4>', '!spell("kageodori", true)')
nmap('<F5>', 'tegatana')
nmap('<F6>', 'omamori')
nmap('<F7>', 'hayai')
nmap('<F8>', '!spell("akshara", true)')
nmap('<F9>', '!spell("kaminari")')
nmap('<F10>', '!spell("arashi")')
nmap('<F11>', '!spell("samusa")')
nmap('<F12>', '!spell("kshira")')

-- TANJIANRUFE

triggers.user:add(triggers.color_line("^<Tanjian>", colors.Blue))

-- TANJIANREPORT

function tanjianreport_setup()
    sendln("tanjianreport $REPORT$ %la %lm %ka %km %vo '%fl' %gi%bl%ta%fr %ko %te %ha %ak %CA %me %ep%lf")
end

--triggers.user:add(triggers.line_func("Report", function (l)
--    m, _, r = string.find(l, "%$REPORT%$ (.*)$")
--    if m then
--        setstatus(r)
--        return ""
--    end
--    return nil
--end), -200)

triggers.user:add(triggers.gsub("%$REPORT%$ (%d+) (%d+) (%d+) (%d+) (%d+) '(.+)' ([JN])([JN])([JN])([JN]) (%w+) ([%+%- ]) (%w+) (%w+) (%w+) ([JjN]) (%d+)", function (la, lm, ka, km, vo, fl, gi, bl, ta, fr, ko, te, ha, ak, ca, me, ep)
    lp = tonumber(la)
    lp_max = tonumber(lm)
    kp = tonumber(ka)
    kp_max = tonumber(km)
    vorsicht = tonumber(vo)
    fluchtrichtung = fl

    if gi == "J" then gift = 1 else gift = 0 end
    if bl == "J" then blind = 1 else blind = 0 end
    if ta == "J" then taub = 1 else blind = 0 end
    if fr == "J" then frosch = 1 else frosch = 0 end
    
    if ko == "ja" then kokoro = 1 else kokoro = 0 end
    if te == "+" then tegatana = 1 elseif te == "-" then tegatana = 2 else tegatana = 0 end
    if ha == "ja" then hayai = 1 else hayai = 0 end
    if ak == "ja" then akshara = 1 elseif ak == "busy" then akshara = 2 else akshara = 0 end
    if me == "J" then meditation = 1 elseif me == "j" then meditation = 2 else meditation = 0 end
    
    gesinnung = ca
    erfahrung = ep

    if type(report) == "function" then
        report()
    else
        report_default()
    end

    return ""
end))

