param()
$ErrorActionPreference = "Continue"
$BulletWhl = (Get-ChildItem "C:\Users\ranas\Desktop\BulletLab\dist\bulletlab-0.3.1-py3-none-any.whl" | Select-Object -First 1).FullName

$versions = @("1.6.0","1.6.3","1.92.0","1.92.3","1.92.4","1.92.5","1.92.600","1.92.601","1.92.700","1.92.801","1.92.900")
$results = [ordered]@{}

foreach ($ver in $versions) {
    $VenvDir = "C:\Users\ranas\Desktop\bl-iso-$ver"
    Write-Host "`n=== imgui-bundle $ver ===" -ForegroundColor Cyan

    # Clean slate venv
    if (Test-Path $VenvDir) { Remove-Item $VenvDir -Recurse -Force -ErrorAction SilentlyContinue }
    py -3.13 -m venv $VenvDir | Out-Null
    $pip = "$VenvDir\Scripts\python.exe"

    # Upgrade pip silently
    & $pip -m pip install --upgrade pip --quiet 2>&1 | Out-Null

    # Pre-install typing_extensions (needed by imgui-bundle 1.6.x's imgui_pydantic.py before deps resolve)
    & $pip -m pip install typing_extensions --quiet 2>&1 | Out-Null

    # Install imgui-bundle with ALL its declared deps (no --no-deps) but binary-only to avoid CMake
    Write-Host "  Installing imgui-bundle==$ver (with deps)..."
    $r = & $pip -m pip install --only-binary=imgui-bundle "imgui-bundle==$ver" --quiet 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  INSTALL_FAIL" -ForegroundColor Red
        $results[$ver] = "INSTALL_FAIL"
        continue
    }
    $installed = & $pip -m pip show imgui-bundle 2>&1 | Select-String "Version:"
    Write-Host "  Installed: $installed"

    # Install BulletLab deps that imgui-bundle 1.92.x moved to optional
    # (PyOpenGL and glfw needed by BulletLab UI regardless of imgui-bundle version)
    & $pip -m pip install "pybullet>=3.2.6" "numpy>=1.24.0" "pandas>=2.0.0" "pyyaml>=6.0" "PyOpenGL>=3.1.0" "glfw" "pytest>=7.4.0" "pytest-cov>=4.1.0" "pytest-mock>=3.11.0" --quiet 2>&1 | Out-Null

    # Install BulletLab wheel (no-deps since we already installed its deps above)
    & $pip -m pip install $BulletWhl --no-deps --quiet 2>&1 | Out-Null

    # Run compat test
    Write-Host "  Running compat test..."
    $compatOut = & $pip "C:\Users\ranas\Desktop\BulletLab\test_compat_v2.py" $ver 2>&1
    $compatExit = $LASTEXITCODE

    # Run pytest
    Write-Host "  Running pytest..."
    $pytestOut = & $pip -m pytest "C:\Users\ranas\Desktop\BulletLab\tests" -q --tb=line 2>&1
    $pytestExit = $LASTEXITCODE
    $pytestSummary = ($pytestOut -split "`n") | Select-Object -Last 3

    # Result
    $status = if ($compatExit -eq 0 -and $pytestExit -eq 0) { "COMPATIBLE" } else { "INCOMPATIBLE" }
    $results[$ver] = $status
    $color = if ($status -eq "COMPATIBLE") { "Green" } else { "Red" }
    Write-Host "  RESULT: $status" -ForegroundColor $color
    Write-Host "  Pytest: $($pytestSummary -join ' | ')"
    
    if ($compatExit -ne 0) {
        $compatOut | Where-Object { $_ -match "^\s+FAIL" } | ForEach-Object { Write-Host "  $_" }
    }
}

Write-Host "`n`n========== COMPATIBILITY MATRIX ==========" -ForegroundColor Yellow
foreach ($ver in $versions) {
    $r = $results[$ver]
    $color = if ($r -eq "COMPATIBLE") { "Green" } elseif ($r -eq "INSTALL_FAIL") { "DarkGray" } else { "Red" }
    Write-Host ("  {0,-12} : {1}" -f "imgui $ver", $r) -ForegroundColor $color
}
Write-Host "==========================================" -ForegroundColor Yellow
