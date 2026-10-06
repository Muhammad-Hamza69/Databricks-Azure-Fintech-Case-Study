param(
    [string]$Repository = 'Muhammad-Hamza69/Databricks-Azure-Fintech-Case-Study'
)

$ErrorActionPreference = 'Stop'

function Invoke-CheckedGit {
    param([string[]]$GitArguments)
    & git @GitArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Git command failed: git $($GitArguments -join ' ')"
    }
}

if ($Repository -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$') {
    throw 'Repository must use owner/repository format.'
}

$sourceDirectory = $PSScriptRoot
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $sourceDirectory '..')).Path
$wikiRemote = "https://github.com/$Repository.wiki.git"
$pageFiles = @('Home.md', 'Case-Study-Blog.md', '_Sidebar.md', '_Footer.md')

foreach ($pageFile in $pageFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $sourceDirectory $pageFile))) {
        throw "Missing wiki source: $pageFile"
    }
}

# Check availability before creating a local clone. GitHub requires the first
# wiki page to be saved through its UI before this Git endpoint exists.
$previousPromptSetting = $env:GIT_TERMINAL_PROMPT
$env:GIT_TERMINAL_PROMPT = '0'
try {
    $wikiRefs = @(& git ls-remote --symref $wikiRemote HEAD 2>&1)
    $remoteExitCode = $LASTEXITCODE
    if ($remoteExitCode -ne 0) {
        throw "Wiki Git endpoint unavailable. With repository write access, create a Home page at https://github.com/$Repository/wiki/_new and rerun this script. Network or authentication failures can also make the endpoint unavailable."
    }
} finally {
    $env:GIT_TERMINAL_PROMPT = $previousPromptSetting
}

$wikiBranch = $null
foreach ($wikiRef in $wikiRefs) {
    if ([string]$wikiRef -match '^ref:\s+refs/heads/(\S+)\s+HEAD$') {
        $wikiBranch = $Matches[1]
        break
    }
}
if (-not $wikiBranch) { throw 'Could not determine the wiki default branch.' }

$recoveryDirectory = Join-Path $repositoryRoot '.git-recovery'
if (-not (Test-Path -LiteralPath $recoveryDirectory)) {
    New-Item -ItemType Directory -Path $recoveryDirectory | Out-Null
}
$wikiCheckout = Join-Path $recoveryDirectory ('wiki-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
Invoke-CheckedGit -GitArguments @('clone', '--branch', $wikiBranch, '--single-branch', $wikiRemote, $wikiCheckout)

Push-Location -LiteralPath $wikiCheckout
try {
    # Keep the previous published pages in a local history backup before updates.
    $bundlePath = $wikiCheckout + '-before-update.bundle'
    Invoke-CheckedGit -GitArguments @('bundle', 'create', $bundlePath, '--all')
    foreach ($pageFile in $pageFiles) {
        Copy-Item -LiteralPath (Join-Path $sourceDirectory $pageFile) -Destination (Join-Path $wikiCheckout $pageFile)
    }
    Invoke-CheckedGit -GitArguments (@('add', '--') + $pageFiles)
    Invoke-CheckedGit -GitArguments @('diff', '--cached', '--check')
    $stagedChanges = @(Invoke-CheckedGit -GitArguments @('diff', '--cached', '--name-only'))
    if ($stagedChanges.Count -gt 0) {
        Invoke-CheckedGit -GitArguments @('commit', '-m', 'Document Vivan e-commerce lakehouse and purchase-propensity case study')
        Invoke-CheckedGit -GitArguments @('push', 'origin', $wikiBranch)
    } else {
        Write-Output 'Wiki pages already match the checked-in sources.'
    }
    $localHead = (Invoke-CheckedGit -GitArguments @('rev-parse', 'HEAD')).Trim()
    $remoteHead = @(Invoke-CheckedGit -GitArguments @('ls-remote', 'origin', "refs/heads/$wikiBranch"))
    if ($remoteHead.Count -ne 1 -or ($remoteHead[0] -split '\s+')[0] -ne $localHead) {
        throw 'Wiki push could not be verified against the remote branch.'
    }
    Write-Output "Wiki verified: https://github.com/$Repository/wiki"
    Write-Output "Previous wiki history backup: $bundlePath"
} finally {
    Pop-Location
}
