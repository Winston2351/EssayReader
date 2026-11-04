$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'Python 3 is required. Install Python from python.org, then run start.ps1 again.' }
$env:ECDICT_CSV = Join-Path $root 'stardict.csv'
if (-not (Test-Path $env:ECDICT_CSV)) {
    $env:ECDICT_CSV = 'C:\Users\john0\AppData\Roaming\GoldenDict\dictionaries\ECDICT\stardict.csv'
}
if (-not (Test-Path $env:ECDICT_CSV)) { throw 'Cannot find stardict.csv. Put it beside start.ps1 or set ECDICT_CSV.' }
if ($python.Name -eq 'py.exe') { & $python.Source -3 (Join-Path $root 'paper_lookup.py') }
else { & $python.Source (Join-Path $root 'paper_lookup.py') }
