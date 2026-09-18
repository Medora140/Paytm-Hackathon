Add-Type -AssemblyName System.Windows.Forms

# 1. Set clipboard to 001_initial_schema.sql
$sqlPath = "c:\Users\Medora Gomes\Desktop\money-docs-decoded\backend\migrations\001_initial_schema.sql"
$sqlContent = Get-Content $sqlPath -Raw
Set-Clipboard -Value $sqlContent
Write-Host "Clipboard set to 001_initial_schema.sql ($($sqlContent.Length) chars)"

# 2. Launch Edge to Supabase SQL editor
$url = "https://supabase.com/dashboard/project/qtcncebuochelpgwqthx/sql/new"
$edgePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$proc = Start-Process $edgePath -ArgumentList $url -PassThru
Write-Host "Launched Edge (PID: $($proc.Id)) to $url"

# 3. Wait for page and editor to load
Write-Host "Waiting 12 seconds for SQL editor to load..."
Start-Sleep -Seconds 12

# 4. Bring Edge to foreground
$wshell = New-Object -ComObject WScript.Shell
$wshell.AppActivate($proc.Id)
Start-Sleep -Seconds 1

# Click into center of window to focus editor if needed
# Or send Tab then paste
# Let's send a click or activate
$wshell.SendKeys("^a")
Start-Sleep -Milliseconds 300
$wshell.SendKeys("{BACKSPACE}")
Start-Sleep -Milliseconds 300
$wshell.SendKeys("^v")
Write-Host "Pasted SQL into editor"
Start-Sleep -Seconds 2

# 5. Execute with Ctrl+Enter
$wshell.SendKeys("^{ENTER}")
Write-Host "Sent Ctrl+Enter to execute SQL migration!"

Start-Sleep -Seconds 8
Write-Host "Done sending execution command."
