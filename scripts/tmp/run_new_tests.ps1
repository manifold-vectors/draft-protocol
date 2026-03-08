Set-Location D:\VECTOR\draft-protocol
python -m pytest tests\test_v1_1_features.py -v --tb=short 2>&1
Write-Host "EXIT: $LASTEXITCODE"
