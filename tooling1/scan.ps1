$ErrorActionPreference = 'Stop'
Get-ChildItem -Recurse -Force freebuff-sites-build | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint } | ForEach-Object { Write-Output ("REPARSE: " + $_.FullName) }
Write-Output 'scan-done'
