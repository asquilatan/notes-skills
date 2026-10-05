<#
.SYNOPSIS
    Extracts all questions and correct answers directly from module questions.md on demand.
.DESCRIPTION
    Scans the module's questions.md file (or lesson files as fallback),
    extracts all covered questions, mid-lesson Q&As, and quiz items,
    and outputs a high-density reference of all tested concepts and correct answers.
.PARAMETER ModuleDir
    Path to the module directory containing questions.md. Defaults to current directory.
#>
param(
    [Parameter(Mandatory=$false, Position=0)]
    [string]$ModuleDir = "."
)

$ErrorActionPreference = "Stop"

$resolvedDir = (Resolve-Path $ModuleDir).Path
$questionsFile = Join-Path $resolvedDir "questions.md"

if (-not (Test-Path $questionsFile)) {
    Write-Output "No questions.md found in $resolvedDir"
    exit 0
}

$rawText = Get-Content -Raw -Encoding utf8 -Path $questionsFile
$lines = $rawText -split "`r?`n"

$totalCount = 0
$currentSection = "General"
$currentQ = $null
$currentAns = $null
$items = [System.Collections.Generic.List[string]]::new()

Write-Output "================================================================="
Write-Output " MODULE QUESTIONS REFERENCE: $(Split-Path $resolvedDir -Leaf)"
Write-Output "================================================================="
Write-Output ""

for ($i = 0; $i -lt $lines.Length; $i++) {
    $line = $lines[$i].Trim()

    # Section header: ## Lesson ... or ## Diagnostic ...
    if ($line -match '^##\s+(.+)$' -and -not ($line -match '^##\s+(Diagnostic Test|Module Comprehensive)')) {
        if ($currentQ -and $currentAns) {
            $items.Add("$currentQ`n  - **Correct Answer**: $currentAns")
            $currentQ = $null
            $currentAns = $null
        }
        if ($items.Count -gt 0) {
            Write-Output "### $currentSection"
            $items | ForEach-Object { 
                Write-Output $_
                Write-Output ""
            }
            $items.Clear()
        }
        $currentSection = $matches[1]
    }
    # Quiz Question header: #### Q...: ...
    elseif ($line -match '^####\s+(Q\d*:\s*.+)') {
        if ($currentQ -and $currentAns) {
            $items.Add("$currentQ`n  - **Correct Answer**: $currentAns")
            $currentQ = $null
            $currentAns = $null
        }
        $currentQ = "- **" + $matches[1] + "**"
        $totalCount++
    }
    # Mid-lesson Q header: ### Q: ...
    elseif ($line -match '^###\s+(Q:\s*.+)') {
        if ($currentQ -and $currentAns) {
            $items.Add("$currentQ`n  - **Correct Answer**: $currentAns")
            $currentQ = $null
            $currentAns = $null
        }
        $currentQ = "- **" + $matches[1] + "**"
        $totalCount++
    }
    # Correct answer line from quiz (supports optional blockquote >)
    elseif ($line -match '^>?\s*-\s*\*\*Correct Answer\*\*:\s*(.+)$') {
        $currentAns = $matches[1].Trim()
    }
    # Answer from Q&A bold opening sentence
    elseif ($currentQ -and (-not $currentAns) -and ($line -match '^\*\*(.+)\*\*$')) {
        $currentAns = $matches[1].Trim()
    }
}

if ($currentQ -and $currentAns) {
    $items.Add("$currentQ`n  - **Correct Answer**: $currentAns")
}

if ($items.Count -gt 0) {
    Write-Output "### $currentSection"
    $items | ForEach-Object { 
        Write-Output $_
        Write-Output ""
    }
}

if ($totalCount -eq 0) {
    Write-Output "No questions recorded in $questionsFile."
} else {
    Write-Output "-----------------------------------------------------------------"
    Write-Output "Total Questions Extracted: $totalCount"
    Write-Output "-----------------------------------------------------------------"
}
