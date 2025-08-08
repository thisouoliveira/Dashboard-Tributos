Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Dashboard Tributario Municipal" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Instalando dependencias..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host ""
Write-Host "Iniciando o dashboard..." -ForegroundColor Green
Write-Host ""
Write-Host "O dashboard sera aberto em: http://localhost:8501" -ForegroundColor Green
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Red
Write-Host ""

streamlit run app-tributos.py 