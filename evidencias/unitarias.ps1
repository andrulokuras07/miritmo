# Corre las pruebas unitarias del Entregable 2 (python -m unittest -v) y muestra cada prueba en dos columnas
# para que el resultado completo quepa en una sola pantalla. Uso: powershell -File evidencias\unitarias.ps1
$salida = cmd /c "python -m unittest discover -s entregable-2\backend\tests -v 2>&1"
$pruebas = $salida | Where-Object { $_ -match ' \.\.\. ' } | ForEach-Object { $_ -replace ' \(test_api\.[^)]*\)', '' }
for ($i = 0; $i -lt $pruebas.Count; $i += 2) { "{0,-66}{1}" -f $pruebas[$i], $(if ($i + 1 -lt $pruebas.Count) { $pruebas[$i + 1] }) }
$salida | Where-Object { $_ -notmatch ' \.\.\. ' -and $_ -ne '' }
