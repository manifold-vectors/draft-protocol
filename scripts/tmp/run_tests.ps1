Set-Location D:\VECTOR\draft-protocol
python -m ruff check src/ tests/ 2>&1
Write-Output "---LINT DONE---"
python -m pytest tests/ --tb=short -q 2>&1
