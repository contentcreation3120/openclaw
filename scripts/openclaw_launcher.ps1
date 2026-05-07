Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$env:PYTHONIOENCODING = "utf-8"
$pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonExe) { $pythonExe = "python" }

# ── Form ────────────────────────────────────────────────────────────────────
$form = New-Object System.Windows.Forms.Form
$form.Text = "OpenClaw — Hybrid AI Router"
$form.Size = New-Object System.Drawing.Size(780, 640)
$form.StartPosition = "CenterScreen"
$form.BackColor = [System.Drawing.Color]::FromArgb(13, 13, 20)
$form.FormBorderStyle = "Sizable"
$form.MinimumSize = New-Object System.Drawing.Size(640, 520)

# ── Header panel ─────────────────────────────────────────────────────────────
$header = New-Object System.Windows.Forms.Panel
$header.Size = New-Object System.Drawing.Size(780, 60)
$header.Location = New-Object System.Drawing.Point(0, 0)
$header.BackColor = [System.Drawing.Color]::FromArgb(18, 18, 28)
$header.Anchor = "Top,Left,Right"
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

# ── Status dots ──────────────────────────────────────────────────────────────
$dotOllama   = New-Object System.Windows.Forms.Label
$dotLmstudio = New-Object System.Windows.Forms.Label
$dotClaude   = New-Object System.Windows.Forms.Label
$dotRouter   = New-Object System.Windows.Forms.Label

function Init-Dot($dot, $text, $x, $y) {
    $dot.Text = "● $text"
    $dot.Font = New-Object System.Drawing.Font("Segoe UI", 8)
    $dot.ForeColor = [System.Drawing.Color]::FromArgb(70, 70, 90)
    $dot.Size = New-Object System.Drawing.Size(150, 18)
    $dot.Location = New-Object System.Drawing.Point($x, $y)
    $header.Controls.Add($dot)
}
Init-Dot $dotOllama   "Ollama"    260 8
Init-Dot $dotLmstudio "LM Studio" 260 30
Init-Dot $dotClaude   "Claude API" 420 8
Init-Dot $dotRouter   "Router"    420 30

# ── Header buttons ───────────────────────────────────────────────────────────
$btnStart = New-Object System.Windows.Forms.Button
$btnStart.Text = "▶ START"
$btnStart.Size = New-Object System.Drawing.Size(84, 20)
$btnStart.Location = New-Object System.Drawing.Point(580, 8)
$btnStart.FlatStyle = "Flat"
$btnStart.FlatAppearance.BorderSize = 0
$btnStart.BackColor = [System.Drawing.Color]::FromArgb(25, 130, 65)
$btnStart.ForeColor = [System.Drawing.Color]::White
$btnStart.Font = New-Object System.Drawing.Font("Segoe UI", 8, [System.Drawing.FontStyle]::Bold)
$btnStart.Cursor = [System.Windows.Forms.Cursors]::Hand
$header.Controls.Add($btnStart)

$btnStop = New-Object System.Windows.Forms.Button
$btnStop.Text = "■ STOP"
$btnStop.Size = New-Object System.Drawing.Size(84, 20)
$btnStop.Location = New-Object System.Drawing.Point(580, 32)
$btnStop.FlatStyle = "Flat"
$btnStop.FlatAppearance.BorderSize = 0
$btnStop.BackColor = [System.Drawing.Color]::FromArgb(140, 30, 30)
$btnStop.ForeColor = [System.Drawing.Color]::White
$btnStop.Font = New-Object System.Drawing.Font("Segoe UI", 8, [System.Drawing.FontStyle]::Bold)
$btnStop.Cursor = [System.Windows.Forms.Cursors]::Hand
$header.Controls.Add($btnStop)

$btnStart.Add_Click({
    Add-ChatLine "system" "Starting servers..."
    $form.Refresh()
    & "$PSScriptRoot\start_servers.ps1" 2>$null
    Start-Sleep 2
    $dotOllama.ForeColor   = [System.Drawing.Color]::FromArgb(50, 220, 100)
    $dotClaude.ForeColor   = [System.Drawing.Color]::FromArgb(50, 220, 100)
    $dotRouter.ForeColor   = [System.Drawing.Color]::FromArgb(50, 220, 100)
    $dotLmstudio.ForeColor = [System.Drawing.Color]::FromArgb(220, 160, 40)
    Add-ChatLine "system" "Ollama online. LM Studio: open it manually and click Start Server."
})

$btnStop.Add_Click({
    Add-ChatLine "system" "Stopping servers..."
    $form.Refresh()
    & "$PSScriptRoot\stop_servers.ps1" 2>$null
    $dotOllama.ForeColor   = [System.Drawing.Color]::FromArgb(70, 70, 90)
    $dotLmstudio.ForeColor = [System.Drawing.Color]::FromArgb(70, 70, 90)
    $dotClaude.ForeColor   = [System.Drawing.Color]::FromArgb(70, 70, 90)
    $dotRouter.ForeColor   = [System.Drawing.Color]::FromArgb(70, 70, 90)
    Add-ChatLine "system" "Local servers stopped."
})

# ── Route badge ──────────────────────────────────────────────────────────────
$routeBadge = New-Object System.Windows.Forms.Label
$routeBadge.Text = ""
$routeBadge.Font = New-Object System.Drawing.Font("Segoe UI", 7, [System.Drawing.FontStyle]::Bold)
$routeBadge.ForeColor = [System.Drawing.Color]::FromArgb(80, 200, 255)
$routeBadge.Size = New-Object System.Drawing.Size(760, 16)
$routeBadge.Location = New-Object System.Drawing.Point(8, 63)
$routeBadge.Anchor = "Top,Left,Right"
$form.Controls.Add($routeBadge)

# ── Chat output ───────────────────────────────────────────────────────────────
$chatBox = New-Object System.Windows.Forms.RichTextBox
$chatBox.Location = New-Object System.Drawing.Point(8, 82)
$chatBox.Size = New-Object System.Drawing.Size(748, 450)
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

Add-ChatLine "system" "OpenClaw ready. Type a prompt and press Enter or Send."
Add-ChatLine "system" "strategy->Claude Sonnet  |  signal->Nemotron  |  journal->GPT-OSS  |  code->Devstral"

# ── Input row ─────────────────────────────────────────────────────────────────
$inputBox = New-Object System.Windows.Forms.TextBox
$inputBox.Location = New-Object System.Drawing.Point(8, 542)
$inputBox.Size = New-Object System.Drawing.Size(640, 28)
$inputBox.Anchor = "Bottom,Left,Right"
$inputBox.BackColor = [System.Drawing.Color]::FromArgb(28, 28, 42)
$inputBox.ForeColor = [System.Drawing.Color]::FromArgb(220, 220, 235)
$inputBox.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$inputBox.BorderStyle = "FixedSingle"
$form.Controls.Add($inputBox)

$btnSend = New-Object System.Windows.Forms.Button
$btnSend.Text = "Send >"
$btnSend.Location = New-Object System.Drawing.Point(656, 540)
$btnSend.Size = New-Object System.Drawing.Size(104, 32)
$btnSend.Anchor = "Bottom,Right"
$btnSend.FlatStyle = "Flat"
$btnSend.FlatAppearance.BorderSize = 0
$btnSend.BackColor = [System.Drawing.Color]::FromArgb(25, 130, 65)
$btnSend.ForeColor = [System.Drawing.Color]::White
$btnSend.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$btnSend.Cursor = [System.Windows.Forms.Cursors]::Hand
$form.Controls.Add($btnSend)

$statusBar = New-Object System.Windows.Forms.Label
$statusBar.Text = "Idle"
$statusBar.Font = New-Object System.Drawing.Font("Segoe UI", 7)
$statusBar.ForeColor = [System.Drawing.Color]::FromArgb(80, 80, 110)
$statusBar.Size = New-Object System.Drawing.Size(760, 16)
$statusBar.Location = New-Object System.Drawing.Point(8, 578)
$statusBar.Anchor = "Bottom,Left,Right"
$form.Controls.Add($statusBar)

# ── Send logic ────────────────────────────────────────────────────────────────
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

    # Get route decision
    $decisionRaw = & $pythonExe -m openclaw explain $prompt 2>&1
    $taskType = ($decisionRaw | Select-String "Task type" | Select-Object -First 1).ToString() -replace ".*Task type\s*:\s*",""
    $model    = ($decisionRaw | Select-String "Model"     | Select-Object -First 1).ToString() -replace ".*Model\s*:\s*",""
    $backend  = ($decisionRaw | Select-String "Backend"   | Select-Object -First 1).ToString() -replace ".*Backend\s*:\s*",""
    $routeBadge.Text = "  [$taskType]  ->  $model  ($backend)"
    $statusBar.Text = "Calling $model..."
    $form.Refresh()

    # Call the router in a background job so UI stays responsive
    $job = Start-Job -ScriptBlock {
        param($exe, $p)
        $env:PYTHONIOENCODING = "utf-8"
        & $exe -m openclaw route $p 2>&1
    } -ArgumentList $pythonExe, $prompt

    while ($job.State -eq "Running") {
        [System.Windows.Forms.Application]::DoEvents()
        Start-Sleep -Milliseconds 200
    }

    $output = Receive-Job $job -ErrorAction SilentlyContinue
    Remove-Job $job -Force

    # Strip loguru timestamp lines, keep only the actual response
    $response = ($output | Where-Object { $_ -notmatch "^\s*\d{4}-\d{2}-\d{2}" -and $_ -notmatch "NativeCommandError" }) -join "`n"
    $response = $response.Trim()

    if ($response) {
        Add-ChatLine "ai" $response
    } else {
        Add-ChatLine "error" "No response. Is Ollama running? Check that your API key is in .env"
    }

    $statusBar.Text = "Done"
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
