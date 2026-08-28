# Run all version compatibility tests sequentially
# Assumes: munch, numpy, PyOpenGL, glfw, pydantic already installed

param()
$versions = @("1.6.0","1.6.3","1.92.0","1.92.3","1.92.4","1.92.5","1.92.600","1.92.601","1.92.700","1.92.801","1.92.900")
$results = @{}

foreach ($ver in $versions) {
    Write-Host "`n=== Installing imgui-bundle $ver ===" -ForegroundColor Cyan
    $installOut = py -3.13 -m pip install --only-binary=:all: --no-deps "imgui-bundle==$ver" --quiet 2>&1
    if ($LASTEXITCODE -ne 0) {
        $results[$ver] = "INSTALL_FAIL"
        Write-Host "Could not install $ver" -ForegroundColor Red
        continue
    }

    $testOut = py -3.13 test_compat_v2.py $ver 2>&1
    $testExit = $LASTEXITCODE
    
    # Extract summary line
    $summaryLine = ($testOut | Where-Object { $_ -match "STATUS:" }) | Select-Object -Last 1
    $passFail = if ($testExit -eq 0) { "COMPATIBLE" } else { "INCOMPATIBLE" }
    $results[$ver] = $passFail
    
    Write-Host "$ver -> $passFail" -ForegroundColor $(if ($passFail -eq "COMPATIBLE") {"Green"} else {"Red"})
    
    # Print only FAIL lines for incompatible ones
    if ($testExit -ne 0) {
        $testOut | Where-Object { $_ -match "FAIL " } | ForEach-Object { Write-Host "  $_" }
    }
}

Write-Host "`n========== FINAL MATRIX ==========" -ForegroundColor Yellow
foreach ($ver in $versions) {
    $r = $results[$ver]
    $color = if ($r -eq "COMPATIBLE") {"Green"} elseif ($r -eq "INSTALL_FAIL") {"DarkRed"} else {"Red"}
    Write-Host "  imgui-bundle $ver : $r" -ForegroundColor $color
}
