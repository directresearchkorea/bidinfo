@echo off
cd /d "%~dp0"
echo ======================================== >> weekly_custom_report_log.txt
echo Running Weekly Custom Report Dispatch at %date% %time% >> weekly_custom_report_log.txt
py execution\send_weekly_custom_report.py >> weekly_custom_report_log.txt 2>&1
echo Finished at %date% %time% >> weekly_custom_report_log.txt
