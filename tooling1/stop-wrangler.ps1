$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'wrangler' -or $_.CommandLine -match 'workerd' }
foreach ($p in $procs) {
  Write-Output ("MATCH pid=" + $p.ProcessId + " parent=" + $p.ParentProcessId + " name=" + $p.Name)
  taskkill /PID $p.ProcessId /F /T | Out-Null
}
Write-Output "done"
