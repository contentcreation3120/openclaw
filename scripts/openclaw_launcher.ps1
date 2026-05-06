Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$env:PYTHONIOENCODING = "utf-8"
$pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source

# ── Form ────────────────────────────────────────────────────────────────────
$form = New-Object System.Windows.Forms.Form
$form.Text = "OpenClaw — Hybrid AI Router"
$form.Size = New-Object System.Drawing.Size(780, 620)
$form.StartPosition = "CenterScreen"
$form.BackColor = [System.Drawing.Color]::FromArgb(13, 13, 20)
$form.FormBorderStyle = "Sizable"
$form.MinimumSize = New-Object System.Drawing.Size(640, 500)

# ── Header ──────────────────────────────────────────────────────────────────
$header = New-Object System.Windows.Forms.Panel
$header.Size = New-Object System.Drawing.Size(780, 60)
$header.Location = New-Object System.Drawing.Point(0, 0)
$header.BackColor = [System.Drawing.Color]::FromArgb(18, 18, 28)
$form.Controls.Add($header)

$title = New-Object System.Windows.Forms.Label
$title.Text = "OPENCLAW"
$title.Font = New-Object System.Drawing.Font("Segoe UI", 16, [System.Drawing.FontStyle]::Bold)
$title.ForeColor = [System.Drawing.Color]::FromArgb(80, 200, 255)
$title.Size = New-Object System.Drawing.Size(200, 36)
$title.Location = New-Object System.Drawing.Point(16, 12)
$header.Controls.Add($title)

$sub = New-Object System.Windows.Forms.Label
$sub.Text = "Local first. Claude when it counts."
$sub.Font = New-Object System.Drawing.Font("Segoe UI", 8)
$sub.ForeColor = [System.Drawing.Color]::FromArgb(90, 90, 120)
$sub.Size = New-Object System.Drawing.Size(220, 18)
$sub.Location = New-Object System.Drawing.Point(18, 40)
$header.Controls.Add($sub)

# ── Status dots ─────────────────────────────────────────────────────────────
function Add-Dot($parent, $x, $y, $label, $key) {
    $dot = New-Object System.Windows.Forms.Label
    $dot.Text = "●  $label"
    $dot.Name = "dot_$key"
    $dot.Font = New-Object System.Drawing.Font("Segoe UI", 8)
    $dot.ForeColor = [System.Drawing.Color]::FromArgb(70, 70, 90)
    $dot.Size = New-Object System.Drawing.Size(160, 18)
    $dot.Location = New-Object System.Drawing.Point($x, $y)
    $parent.Controls.Add($dot)
}
Add-Dot $header 260 10  "Ollama" "ollama"
Add-Dot $header 260 30  "LM Studio" "lmstudio"
Add-Dot $header 420 10  "Claude API" "claude"
Add-Dot $header 420 30  "Router" "router"

# ── Server buttons ──────────────────────────────────────────────────────────
function Make-Btn($parent, $text, $x, $y, $w, $h, $bg) {
    $b = New-Object System.Windows.Forms.Button
    $b.Text = $text
    $b.Size = New-Object System.Drawing.Size($w, $h)
    $b.Location = New-Object System.Drawing.Point($x, $y)
    $b.FlatStyle = "Flat"
    $b.FlatAppearance.BorderSize = 0
    $b.BackColor = $bg
    $b.ForeColor = [System.Drawing.Color]::White
    $b.Font = New-Object System.Drawing.Font("Segoe UI", 8, [System.Drawing.FontStyle]::Bold)
    $b.Cursor = [System.Windows.Forms.Cursors]::Hand
    $parent.Controls.Add($b)
    return $b
}

$btnStart = Make-Btn $header "▶ START" 590 10 80 18 ([System.Drawing.Color]::FromArgb(25, 130, 65))
$btnStop  = Make-Btn $header "■ STOP"  590 32 80 18 ([System.Drawing.Color]::FromArgb(140, 30, 30))

$btnStart.Add_Click({
    & "$PSScriptRoot\start_servers.ps1" 2>$null
    Start-Sleep 2
    ($form.Controls | ForEach-Object { $_.Controls } | Where-Object { $_.Name -eq "dot_ollama" }).ForeColor   = [System.Drawing.Color]::FromArgb(50, 220, 100)
    ($form.Controls | ForEach-Object { $_.Controls } | Where-Object { $_.Name -eq "dot_claude" }).ForeColor   = [System.Drawing.Color]::FromArgb(50, 220, 100)
    ($form.Controls | ForEach-Object { $_.Controls } | Where-Object { $_.Name -eq "dot_router" }).ForeColor   = [System.Drawing.Color]::FromArgb(50, 220, 100)
    ($form.Controls | ForEach-Object { $_.Controls } | Where-Object { $_.Name -eq "dot_lmstudio" }).ForeColor = [System.Drawing.Color]::FromArgb(220, 160, 40)
    Add-ChatLine "system" "Servers started. Ollama online. LM Studio: open it and click Start Server."
})

$btnStop.Add_Click({
    & "$PSScriptRoot\stop_servers.ps1" 2>$null
    @("ollama","lmstudio","claude","router") | ForEach-Object {
        ($form.Controls | ForEach-Object { $_.Controls } | Where-Object { $_.Name -eq "dot_$_" }).ForeColor = [System.Drawing.Color]::FromArgb(70,70,90)
    }
    Add-ChatLine "system" "Local servers stopped."
})

# ── Route badge label ────────────────────────────────────────────────────────
$routeBadge = New-Object System.Windows.Forms.Label
$routeBadge.Text = ""
$routeBadge.Font = New-Object System.Drawing.Font("Segoe UI", 7, [System.Drawing.FontStyle]::Bold)
$routeBadge.ForeColor = [System.Drawing.Color]::FromArgb(80, 200, 255)
$routeBadge.Size = New-Object System.Drawing.Size(680, 16)
$routeBadge.Location = New-Object System.Drawing.Point(8, 62)
$routeBadge.TextAlign = "MiddleLeft"
$form.Controls.Add($routeBadge)

# ── Chat output ──────────────────────────────────────────────────────────────
$chatBox = New-Object System.Windows.Forms.RichTextBox
$chatBox.Location = New-Object System.Drawing.Point(8, 82)
$chatBox.Size = New-Object System.Drawing.Size(748, 400)
$chatBox.Anchor = "Top,Left,Right,Bottom"
$chatBox.BackColor = [System.Drawing.Color]::FromArgb(13, 13, 20)
$chatBox.ForeColor = [System.Drawing.Color]::FromArgb(220, 220, 235)
$chatBox.Font = New-Object System.Drawing.Font("Consolas", 9)
$chatBox.ReadOnly = $true
$chatBox.BorderStyle = "None"
$chatBox.ScrollBars = "Vertical"
$form.Controls.Add($chatBox)

function Add-ChatLine($role, $text) {
    $chatBox.SelectionStart = $chatBox.TextLength
    $chatBox.SelectionLength = 0
    switch ($role) {
        "you"    { $chatBox.SelectionColor = [System.Drawing.Color]::FromArgb(80,200,255);  $chatBox.AppendText("You: ") }
        "ai"     { $chatBox.SelectionColor = [System.Drawing.Color]::FromArgb(80,230,140);  $chatBox.AppendText("AI:  ") }
        "system" { $chatBox.SelectionColor = [System.Drawing.Color]::FromArgb(150,150,80);  $chatBox.AppendText("---  ") }
        "error"  { $chatBox.SelectionColor = [System.Drawing.Color]::FromArgb(230,80,80);   $chatBox.AppendText("ERR: ") }
    }
    $chatBox.SelectionColor = [System.Drawing.Color]::FromArgb(220, 220, 235)
    $chatBox.AppendText("$text`n")
    $chatBox.ScrollToCaret()
}

Add-ChatLine "system" "OpenClaw ready. Type a prompt below and press Enter or click Send."
Add-ChatLine "system" "Routes: strategy->Claude  |  code->Devstral  |  signal/journal->Ollama"

# ── Input row ────────────────────────────────────────────────────────────────
$inputPanel = New-Object System.Windows.Forms.Panel
$inputPanel.Location = New-Object System.Drawing.Point(8, 492)
$inputPanel.Size = New-Object System.Drawing.Size(748, 36)
$inputPanel.Anchor = "Bottom,Left,Right"
$inputPanel.BackColor = [System.Drawing.Color]::FromArgb(22, 22, 35)
$form.Controls.Add($inputPanel)

$inputBox = New-Object System.Windows.Forms.TextBox
$inputBox.Location = New-Object System.Drawing.Point(0, 0)
$inputBox.Size = New-Object System.Drawing.Size(640, 36)
$inputBox.Anchor = "Left,Right"
$inputBox.BackColor = [System.Drawing.Color]::FromArgb(22, 22, 35)
$inputBox.ForeColor = [System.Drawing.Color]::FromArgb(220, 220, 235)
$inputBox.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$inputBox.BorderStyle = "None"
$inputBox.PlaceholderText = "Ask anything about your trades, signals, or code..."
$inputPanel.Controls.Add($inputBox)

$btnSend = New-Object System.Windows.Forms.Button
$btnSend.Text = "Send  >"
$btnSend.Location = New-Object System.Drawing.Point(644, 0)
$btnSend.Size = New-Object System.Drawing.Size(104, 36)
$btnSend.Anchor = "Right"
$btnSend.FlatStyle = "Flat"
$btnSend.FlatAppearance.BorderSize = 0
$btnSend.BackColor = [System.Drawing.Color]::FromArgb(25, 130, 65)
$btnSend.ForeColor = [System.Drawing.Color]::White
$btnSend.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$btnSend.Cursor = [System.Windows.Forms.Cursors]::Hand
$inputPanel.Controls.Add($btnSend)

# ── Status bar ───────────────────────────────────────────────────────────────
$statusBar = New-Object System.Windows.Forms.Label
$statusBar.Text = "Idle"
$statusBar.Font = New-Object System.Drawing.Font("Segoe UI", 7)
$statusBar.ForeColor = [System.Drawing.Color]::FromArgb(80, 80, 110)
$statusBar.Size = New-Object System.Drawing.Size(748, 16)
$statusBar.Location = New-Object System.Drawing.Point(8, 534)
$statusBar.Anchor = "Bottom,Left,Right"
$form.Controls.Add($statusBar)

# ── Send logic ───────────────────────────────────────────────────────────────
$script:busy = $false

function Send-Prompt {
    if ($script:busy) { return }
    $prompt = $inputBox.Text.Trim()
    if (-not $prompt) { return }

    $inputBox.Clear()
    $script:busy = $true
    $btnSend.Enabled = $false
    $statusBar.Text = "Routing..."
    $form.Refresh()

    Add-ChatLine "you" $prompt

    # Get route decision first
    $decisionRaw = & $pythonExe -m openclaw explain $prompt 2>&1
    $taskType = ($decisionRaw | Select-String "Task type").ToString() -replace ".*Task type\s*:\s*", ""
    $model    = ($decisionRaw | Select-String "Model").ToString()     -replace ".*Model\s*:\s*", ""
    $backend  = ($decisionRaw | Select-String "Backend").ToString()   -replace ".*Backend\s*:\s*", ""
    $routeBadge.Text = "  Route: [$taskType]  ->  $model  ($backend)"

    $statusBar.Text = "Calling $model..."
    $form.Refresh()

    # Run the actual route call
    $job = Start-Job -ScriptBlock {
        param($exe, $p)
        $env:PYTHONIOENCODING = "utf-8"
        & $exe -m openclaw route $p 2>&1
    } -ArgumentList $pythonExe, $prompt

    # Poll until done (keeps UI responsive)
    while ($job.State -eq "Running") {
        [System.Windows.Forms.Application]::DoEvents()
        Start-Sleep -Milliseconds 200
    }

    $output = Receive-Job $job -ErrorAction SilentlyContinue
    Remove-Job $job -Force

    # Strip loguru lines
    $response = ($output | Where-Object { $_ -notmatch "^\s*\d{4}-\d{2}-\d{2}.*\|" }) -join "`n"
    $response = $response.Trim()

    if ($response) {
        Add-ChatLine "ai" $response
    } else {
        Add-ChatLine "error" "No response — check that Ollama is running or Claude API key is set."
    }

    $statusBar.Text = "Done.  Total calls today tracked in D:\CLAUDE\logs"
    $script:busy = $false
    $btnSend.Enabled = $true
    $inputBox.Focus()
}

$btnSend.Add_Click({ Send-Prompt })
$inputBox.Add_KeyDown({
    if ($_.KeyCode -eq "Return") {
        $_.SuppressKeyPress = $true
        Send-Prompt
    }
})

$inputBox.Focus()
$form.ShowDialog() | Out-Null
