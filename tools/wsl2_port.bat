@echo off
set PORT=8000
set DISTRO=Ubuntu

REM Get WSL IP
FOR /F "tokens=1" %%i IN ('wsl -d %DISTRO% hostname -I') DO set WSL_IP=%%i

IF "%WSL_IP%"=="" (
    echo [ERROR] WSL2 IP를 가져올 수 없습니다. WSL이 실행 중인지 확인하세요.
    exit /b 1
)

echo [INFO] WSL2 IP: %WSL_IP%

REM Remove existing portproxy rule
netsh interface portproxy delete v4tov4 listenport=%PORT% listenaddress=0.0.0.0

REM Add new portproxy rule
netsh interface portproxy add v4tov4 listenport=%PORT% listenaddress=0.0.0.0 connectport=%PORT% connectaddress=%WSL_IP%

REM Add firewall rule (first time only; silently fail if exists)
netsh advfirewall firewall add rule name="Allow WSL2 Port %PORT%" dir=in action=allow protocol=TCP localport=%PORT% >nul 2>&1

echo [INFO] 포트포워딩 완료: Windows:0.0.0.0:%PORT% → WSL2:%WSL_IP%:%PORT%
