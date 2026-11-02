@echo off
REM HYDRA_UMC_SCRIPT_STANDARD_HEADER_BEGIN
REM *****************************************************************************
REM Project   : HYDRA-UMC-DEVELOPER-NODE
REM Script    : run.bat
REM Purpose   : Runtime workflow for the project entry point.
REM Author    : JuanenRac (Electro Hobby 3D)
REM Email     : electrohobby3d@gmail.com
REM Copyright : (C) 2026 JuanenRac
REM License   : GPL-3.0-or-later - see LICENSE
REM *****************************************************************************
REM HYDRA_UMC_SCRIPT_STANDARD_HEADER_END
REM HYDRA_UMC_SCRIPT_STANDARD_BANNER_BEGIN
echo.
echo *****************************************************************************
echo * HYDRA-UMC-DEVELOPER-NODE - run.bat
echo * Mode      : RUN WORKFLOW
echo * Author    : JuanenRac (Electro Hobby 3D)
echo * Email     : electrohobby3d@gmail.com
echo * Copyright : (C) 2026 JuanenRac
echo * License   : GPL-3.0-or-later - see LICENSE
echo * ------------------------------------------------------------------------- *
echo * 1. Resolve the runtime prerequisites declared by this script.
echo * 2. Start the project entry point and forward user arguments unchanged.
echo * 3. Preserve its result and keep an interactive terminal open.
echo *****************************************************************************
echo.
REM HYDRA_UMC_SCRIPT_STANDARD_BANNER_END
REM Runs HYDRA-UMC-DEVELOPER-NODE. Run build.bat first.
REM
REM Usage:
REM   run.bat                                        - real demo: checks the shipped
REM                                                     configuration (every switch closed)
REM   run.bat --config configs\developer-node.json evidence verify bundle.json
REM This is a CLI-only delivery - see cli.py's own header comment.
setlocal enabledelayedexpansion
cd /d "%~dp0"

if exist .venv\Scripts\python.exe (
    set "HYDRA_UMC_PY=.venv\Scripts\python.exe"
) else (
    set "HYDRA_UMC_PY=python"
)

if "%~1"=="" (
    echo No arguments given - running a real demo: checking the shipped configuration.
    "!HYDRA_UMC_PY!" -m hydra_umc_developer_node.cli --config configs\developer-node.json config check
) else (
    "!HYDRA_UMC_PY!" -m hydra_umc_developer_node.cli %*
)

:done
set "HYDRA_UMC_RC=!ERRORLEVEL!"
if not defined HYDRA_UMC_CI if "%~1"=="" pause
exit /b !HYDRA_UMC_RC!
