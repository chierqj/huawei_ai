pushd %CD%
python -m ballclient.main %1 %2 %3 > ../log/result.txt
REM python -m ballclient.main %1 %2 %3
pause
popd

EXIT