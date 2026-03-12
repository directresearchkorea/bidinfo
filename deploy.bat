@echo off
echo ========================================
echo  Direct Research Korea - Bid Intelligence
echo  Web Deployment Tool
echo ========================================
echo.
echo [1/2] Preparing Domain...
echo drk-bids.surge.sh > CNAME

echo [2/2] Connecting to Cloud Server...
echo.
echo IMPORTANT: If this is your first time, it might ask for email and password.
echo.

call npx.cmd -y surge . drk-bids.surge.sh

echo.
echo ----------------------------------------
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Your Dashboard is LIVE!
    echo URL: https://drk-bids.surge.sh
) else (
    echo [ERROR] Deployment failed. Please check your internet or login info.
)
echo ----------------------------------------
echo.
pause
