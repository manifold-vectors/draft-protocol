Set-Location D:\VECTOR\draft-protocol
python -m ruff check src\draft_protocol\engine.py src\draft_protocol\server.py src\draft_protocol\__init__.py
Write-Host "EXIT: $LASTEXITCODE"
