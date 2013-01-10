local M = {}

local esc = "\27"

M.Off = esc .. "[0m"
M.Black = esc .. "[30m"
M.Red = esc .. "[31m"
M.Green = esc .. "[32m"
M.Yellow = esc .. "[33m"
M.Blue = esc .. "[34m"
M.Magenta = esc .. "[35m"
M.Cyan = esc .. "[36m"
M.White = esc .. "[37m"

return M
