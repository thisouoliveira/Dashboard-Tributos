@echo off
echo ========================================
echo    Dashboard Tributario Municipal
echo ========================================
echo.
echo Instalando dependencias...
pip install -r requirements.txt
echo.
echo Iniciando o dashboard...
echo.
echo O dashboard sera aberto em: http://localhost:8501
echo.
echo Pressione Ctrl+C para parar o servidor
echo.
streamlit run app-tributos.py
pause 