Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "OpenClaw — Hybrid AI Router"
$form.Size = New-Object System.Drawing.Size(420, 380)
$form.StartPosition = "CenterScreen"
$form.BackColor = [System.Drawing.Color]::FromArgb(15, 15, 22)
$form.FormBorderStyle = "FixedSingle"
$form.MaximizeBox = $false

$title = New-Object System.Windows.Forms.Label
$title.Text = "OPENCLAW"
$title.Font = New-Object System.Drawing.Font("Segoe UI", 18, [System.Drawing.FontStyle]::Bold)
$title.ForeColor = [System.Drawing.Color]::FromArgb(80, 200, 255)
$title.Size = New-Object System.Drawing.Size(400, 40)
$title.Location = New-Object System.Drawing.Point(10, 15)
$title.TextAlign = "MiddleCenter"
$form.Controls.Add($title)

$sub = New-Object System.Windows.Forms.Label
$sub.Text = "Hybrid AI Router  |  Local first. Claude when it counts."
$sub.Font = New-Object System.Drawing.Font("Segoe UI", 8)
$sub.ForeColor = [System.Drawing.Color]::FromArgb(100,100,130)
$sub.Size = New-Object System.Drawing.Size(400, 20)
$sub.Location = New-Object System.Drawing.Point(10, 55)
$sub.TextAlign = "MiddleCenter"
$form.Controls.Add($sub)

function Add-StatusRow($y, $label, $key) {
    $lbl = New-Object System.Windows.Forms.Label
    $lbl.Text = $label; $lbl.ForeColor = [System.Drawing.Color]::White
    $lbl.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
    $lbl.Size = New-Object System.Drawing.Size(160, 24); $lbl.Location = New-Object System.Drawing.Point(30, $y)
    $form.Controls.Add($lbl)
    $dot = New-Object System.Windows.Forms.Label
    $dot.Text = "●"; $dot.Name = "dot_$key"
    $dot.Font = New-Object System.Drawing.Font("Segoe UI", 12)
    $dot.ForeColor = [System.Drawing.Color]::FromArgb(60,60,80)
    $dot.Size = New-Object System.Drawing.Size(30, 24); $dot.Location = New-Object System.Drawing.Point(200, $y)
    $form.Controls.Add($dot)
}

Add-StatusRow 90  "Ollama   (GPT-OSS + Nemotron)" "ollama"
Add-StatusRow 120 "LM Studio  (Devstral code)" "lmstudio"
Add-StatusRow 150 "Claude API  (strategy fallback)" "claude"

$status = New-Object System.Windows.Forms.Label
$status.Text = "Status: Idle"
$status.Font = New-Object System.Drawing.Font("Segoe UI", 8)
$status.ForeColor = [System.Drawing.Color]::FromArgb(150,150,180)
$status.Size = New-Object System.Drawing.Size(380, 20)
$status.Location = New-Object System.Drawing.Point(20, 185)
$form.Controls.Add($status)

$sep = New-Object System.Windows.Forms.Label
$sep.BackColor = [System.Drawing.Color]::FromArgb(50,50,70)
$sep.Size = New-Object System.Drawing.Size(380, 1)
$sep.Location = New-Object System.Drawing.Point(20, 210)
$form.Controls.Add($sep)

function Make-Btn($text, $x, $y, $w, $h, $bg, $fg) {
    $b = New-Object System.Windows.Forms.Button
    $b.Text = $text; $b.Size = New-Object System.Drawing.Size($w,$h)
    $b.Location = New-Object System.Drawing.Point($x,$y)
    $b.FlatStyle = "Flat"; $b.FlatAppearance.BorderSize = 0
    $b.BackColor = $bg; $b.ForeColor = $fg
    $b.Font = New-Object System.Drawing.Font("Segoe UI",11,[System.Drawing.FontStyle]::Bold)
    $b.Cursor = [System.Windows.Forms.Cursors]::Hand
    return $b
}

$btnStart = Make-Btn "▶  START" 20 225 175 55 ([System.Drawing.Color]::FromArgb(25,140,70)) ([System.Drawing.Color]::White)
$btnStart.Add_Click({
    $status.Text = "Starting local servers..."; $form.Refresh()
    & "$PSScriptRoot\start_servers.ps1" 2>$null
    Start-Sleep 2
    ($form.Controls | Where-Object { $_.Name -eq "dot_ollama" }).ForeColor = [System.Drawing.Color]::FromArgb(50,220,100)
    ($form.Controls | Where-Object { $_.Name -eq "dot_lmstudio" }).ForeColor = [System.Drawing.Color]::FromArgb(220,180,50)
    ($form.Controls | Where-Object { $_.Name -eq "dot_claude" }).ForeColor = [System.Drawing.Color]::FromArgb(50,220,100)
    $status.Text = "Ollama online. LM Studio open -- load Devstral + Start Server."
})
$form.Controls.Add($btnStart)

$btnStop = Make-Btn "■  STOP" 215 225 175 55 ([System.Drawing.Color]::FromArgb(160,35,35)) ([System.Drawing.Color]::White)
$btnStop.Add_Click({
    $status.Text = "Stopping servers..."; $form.Refresh()
    & "$PSScriptRoot\stop_servers.ps1" 2>$null
    @("ollama","lmstudio","claude") | ForEach-Object {
        ($form.Controls | Where-Object { $_.Name -eq "dot_$_" }).ForeColor = [System.Drawing.Color]::FromArgb(60,60,80)
    }
    $status.Text = "All local servers stopped."
})
$form.Controls.Add($btnStop)

$routing = New-Object System.Windows.Forms.Label
$routing.Text = "journal/general -> GPT-OSS  |  signal/brief -> Nemotron  |  code -> Devstral  |  strategy -> Claude"
$routing.Font = New-Object System.Drawing.Font("Segoe UI", 7)
$routing.ForeColor = [System.Drawing.Color]::FromArgb(80,80,110)
$routing.Size = New-Object System.Drawing.Size(390, 30)
$routing.Location = New-Object System.Drawing.Point(10, 295)
$routing.TextAlign = "MiddleCenter"
$form.Controls.Add($routing)

$form.ShowDialog() | Out-Null
