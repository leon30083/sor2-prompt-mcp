Param(
    [string]$Report = "test-report.txt"
)

Write-Host "[Run] 開始執行 pytest 測試..." -ForegroundColor Cyan

# 建議在 Windows 11 下使用 Python3 與已安裝 pytest
python -m pytest -q | Tee-Object -FilePath $Report

if ($LASTEXITCODE -eq 0) {
    Write-Host "[Run] 所有測試通過 ✅" -ForegroundColor Green
} else {
    Write-Host "[Run] 測試有失敗或錯誤 ❌，請查看 $Report" -ForegroundColor Red
}