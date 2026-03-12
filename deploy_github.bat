@echo off
echo ========================================
echo  Direct Research Korea - Bid Intelligence
echo  GitHub Pages Deployment Tool
echo ========================================
echo.

:: Check if git is installed
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Git is not installed or not in PATH. Please install Git first.
    pause
    exit /b
)

:: Ensure it's a git repo
if not exist ".git" (
    echo [INFO] Initializing Git repository...
    git init
    git branch -M main
    echo.
    echo [WARNING] You have not connected this to GitHub yet!
    echo Please run the following command once to connect your GitHub repo:
    echo git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
    echo.
    pause
    exit /b
)

echo [1/3] Adding files to Git...
git add .

echo [2/3] Committing changes...
git commit -m "Auto-deploy update: %date% %time%"

echo [3/3] Pushing to GitHub (this will trigger GitHub Pages)...
git push origin main

echo.
echo ----------------------------------------
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Your Dashboard changes have been pushed!
    echo It may take a minute or two for GitHub Pages to update.
    echo Check your repository page for the exact URL.
) else (
    echo [ERROR] Git push failed. Please check your internet, permissions, or if you connected the remote repository correctly.
)
echo ----------------------------------------
echo.
pause
