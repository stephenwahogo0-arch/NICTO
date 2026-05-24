@echo off
REM Build NIKTO Core Engine (Rust ECS + wgpu GPU renderer)
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > nul 2>&1
set CC=cl.exe
set CC_x86_64_msvc=cl.exe
set RUSTFLAGS=-Ctarget-feature=+crt-static
set CARGO_BIN=%USERPROFILE%\.rustup\toolchains\stable-x86_64-pc-windows-msvc\bin
set PATH=%CARGO_BIN%;%PATH%
echo Building nikto-core-engine (this may take 10-15 minutes)...
%CARG_BIN%\cargo.exe build --jobs 1 %*
if %ERRORLEVEL% EQU 0 (
    echo === BUILD SUCCESS ===
    copy /Y target\debug\nikto_core_engine.dll ..\nikto-core-engine.pyd > nul 2>&1
    echo Copied to nikto-core-engine.pyd
) else (
    echo === BUILD FAILED (exit code %ERRORLEVEL%) ===
)
