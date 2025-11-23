@echo off
setlocal enabledelayedexpansion
REM Simple run: 10 conv (1×) via protected .so in Core/

set ROOT=%~dp0
set "PYTHONPATH=%PYTHONPATH%;%ROOT%Core"
if "%DATA_DIR%"=="" set "DATA_DIR=%ROOT%data"
if "%MODELS_DIR%"=="" set "MODELS_DIR=%ROOT%models"
if "%RESULTS_DIR%"=="" set "RESULTS_DIR=%ROOT%results"
REM Ollama для расширения синонимов
if "%OLLAMA_BASE_URL%"=="" set "OLLAMA_BASE_URL=http://localhost:11434"
if "%OLLAMA_URL%"=="" set "OLLAMA_URL=%OLLAMA_BASE_URL%"

if not exist "%RESULTS_DIR%" mkdir "%RESULTS_DIR%"

if "%OPENAI_API_KEY%"=="" (
  echo OPENAI_API_KEY is required
  exit /b 1
)

for /l %%C in (0,1,9) do (
  echo === Conversation %%C ===
  set "LOCOMO_CONV_INDEX=%%C"
  set "SEED=2001"
  python -c "import vac_memory_system_v1_test_locomo as m; m.run_pipeline_v4()"

  REM Санитизируем summary в последнем файле результатов для данного конвоя
  set "LATEST="
  for /f "delims=" %%F in ('dir /b /o:-d "%RESULTS_DIR%\vac_v1_conv%%C_seed%SEED%_*.json" 2^>nul') do (
    set "LATEST=%RESULTS_DIR%\%%F"
    goto :sanitize_loop
  )
:sanitize_loop
  if defined LATEST (
    echo Sanitizing summary in %LATEST%
    python "%ROOT%code\sanitize_summary.py" "%LATEST%" || rem ignore errors
  )
)

echo Done.
endlocal
