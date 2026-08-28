param([string]$Version)
$ErrorActionPreference = "Continue"
$VenvDir = "C:\Users\ranas\Desktop\bl-compat-test-$Version"
$Whl = Get-ChildItem "C:\Users\ranas\Desktop\BulletLab\dist\bulletlab-0.3.1-py3-none-any.whl" | Select-Object -First 1

Write-Host "`n==============================" -ForegroundColor Cyan
Write-Host "Testing imgui-bundle $Version" -ForegroundColor Cyan
Write-Host "==============================`n" -ForegroundColor Cyan

# Create venv
if (Test-Path $VenvDir) { Remove-Item $VenvDir -Recurse -Force }
py -3.13 -m venv $VenvDir | Out-Null
$pip = "$VenvDir\Scripts\python.exe"

# Upgrade pip silently
& $pip -m pip install --upgrade pip --quiet 2>&1 | Out-Null

# Install specific imgui-bundle version (binary only)
Write-Host "Installing imgui-bundle==$Version ..."
$r = & $pip -m pip install --only-binary=:all: --no-deps "imgui-bundle==$Version" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: Could not install imgui-bundle==$Version (no binary wheel?)" -ForegroundColor Red
    Write-Output "WHEEL_FAIL"
    exit 1
}
Write-Host "imgui-bundle $Version installed OK"

# Install BulletLab wheel (no-deps to keep imgui-bundle pinned)
Write-Host "Installing BulletLab wheel (no-deps)..."
& $pip -m pip install $Whl.FullName --no-deps --quiet 2>&1 | Out-Null

# Install remaining deps (except imgui-bundle)
& $pip -m pip install "pybullet>=3.2.6" "numpy>=1.24.0" "pandas>=2.0.0" "pyyaml>=6.0" "PyOpenGL>=3.1.0" "pytest>=7.4.0" "pytest-cov>=4.1.0" "pytest-mock>=3.11.0" --quiet 2>&1 | Out-Null

# Run compat test
Write-Host "Running compat test..."
$compatOut = & $pip "C:\Users\ranas\Desktop\BulletLab\test_compat.py" $Version 2>&1
$compatExit = $LASTEXITCODE
Write-Host $compatOut

# Run pytest
Write-Host "Running pytest..."
$pytestOut = & $pip -m pytest "C:\Users\ranas\Desktop\BulletLab\tests" -q --tb=short 2>&1
$pytestExit = $LASTEXITCODE
# Show last 10 lines
$pytestLines = $pytestOut -split "`n"
$pytestSummary = $pytestLines | Select-Object -Last 5
Write-Host ($pytestSummary -join "`n")

Write-Host "`n--- SUMMARY for $Version ---"
if ($compatExit -eq 0 -and $pytestExit -eq 0) {
    Write-Host "COMPATIBLE" -ForegroundColor Green
    Write-Output "COMPATIBLE:$Version"
} else {
    Write-Host "INCOMPATIBLE (compat=$compatExit pytest=$pytestExit)" -ForegroundColor Red
    Write-Output "INCOMPATIBLE:$Version:compat=$compatExit:pytest=$pytestExit"
}
