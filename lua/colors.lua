local M = {}

local esc = "\27"

M.Off = esc .. "[0m"
M.Red = esc .. "[31m"
M.Green = esc .. "[32m"
M.Blue = esc .. "[34m"

return M
