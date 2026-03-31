@echo off
cd /d "%~dp0"
echo ======================================== >> weekly_summary_log.txt
echo Running Weekly Summary Email Dispatch at %date% %time% >> weekly_summary_log.txt
py execution\send_weekly_summary.py >> weekly_summary_log.txt 2>&1
echo Finished at %date% %time% >> weekly_summary_log.txt
