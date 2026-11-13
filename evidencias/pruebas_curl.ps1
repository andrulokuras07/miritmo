# Pruebas de aceptación de MiRitmo (Entregable 1) con curl contra la URL pública de la Lambda.
# Muestra solo el código HTTP y el mensaje; los tokens nunca se imprimen.
# Crea dos cuentas de prueba (pruebaA-/pruebaB-<marca>@miritmo.mx) con contraseñas aleatorias.
# Uso: powershell -ExecutionPolicy Bypass -File evidencias\pruebas_curl.ps1
param([string]$Api = "https://jaqdhe4yffqneg5kw2khwzz3pm0gztrw.lambda-url.us-east-2.on.aws")

[Console]::OutputEncoding = [Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"
$tmp = Join-Path $env:TEMP ("miritmo-" + [guid]::NewGuid().ToString("N") + ".json")
$utf8 = New-Object Text.UTF8Encoding($false)
$script:ok = 0; $script:total = 0

function Llamar($metodo, $ruta, $cuerpo, $token) {
    $opts = @("-s", "-X", $metodo, "$Api$ruta", "-H", "content-type: application/json", "-w", "`n%{http_code}")
    if ($token) { $opts += @("-H", "authorization: Bearer $token") }
    if ($null -ne $cuerpo) {
        [IO.File]::WriteAllText($tmp, ($cuerpo | ConvertTo-Json -Compress), $utf8)
        $opts += @("--data-binary", "@$tmp")
    }
    $salida = (& curl.exe @opts) -join "`n"
    $i = $salida.LastIndexOf("`n")
    $json = $null
    try { $json = $salida.Substring(0, $i) | ConvertFrom-Json } catch {}
    return @{ codigo = [int]$salida.Substring($i + 1); json = $json }
}

function Mostrar($req, $prueba, $r, $esperado, $extra = "") {
    $script:total++
    $msg = if ($r.json.error) { $r.json.error } elseif ($r.json.token) { "token recibido (oculto)" } elseif ($r.json.registro) { "calificación " + $r.json.registro.calificacion } else { "" }
    $bien = ($r.codigo -eq $esperado) -and ($extra -eq "" -or $msg -eq $extra)
    if ($bien) { $script:ok++ }
    $marca = if ($bien) { "OK " } else { "MAL" }
    $color = if ($bien) { "Green" } else { "Red" }
    Write-Host ("[{0}] {1,-7} {2,-58} HTTP {3}  {4}" -f $marca, $req, $prueba, $r.codigo, $msg) -ForegroundColor $color
}

function Clave() { -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 14 | ForEach-Object { [char]$_ }) }

$marca = Get-Date -Format "yyyyMMddHHmmss"
$a = "pruebaA-$marca@miritmo.mx"; $b = "pruebaB-$marca@miritmo.mx"
$claveA = Clave; $claveB = Clave
$hoy = [DateTime]::UtcNow.AddHours(-6).Date
$fHoy = $hoy.ToString("yyyy-MM-dd"); $fFutura = $hoy.AddDays(1).ToString("yyyy-MM-dd"); $fVieja = $hoy.AddDays(-7).ToString("yyyy-MM-dd")
$dia = @{ horas_trabajo = 6; tareas = 4; horas_sueno = 7.5; energia = 4 }

Write-Host "MiRitmo - pruebas con curl contra $Api" -ForegroundColor Cyan
Write-Host "Hoy (CDMX): $fHoy`n"

Mostrar "RF-01" "Crear cuenta nueva" (Llamar POST "/cuentas" @{ nombre = "Prueba A"; correo = $a; contrasena = $claveA }) 201
Mostrar "RF-01" "Crear cuenta con el mismo correo" (Llamar POST "/cuentas" @{ nombre = "Prueba A"; correo = $a; contrasena = $claveA }) 409
Mostrar "RF-01" "Crear cuenta con contraseña de 7 caracteres" (Llamar POST "/cuentas" @{ nombre = "Prueba C"; correo = "pruebaC-$marca@miritmo.mx"; contrasena = "abc1234" }) 400

$login = Llamar POST "/sesiones" @{ correo = $a; contrasena = $claveA }
Mostrar "RF-02" "Iniciar sesión con datos correctos" $login 200
$tokenA = $login.json.token
Mostrar "RF-02" "Iniciar sesión con contraseña incorrecta" (Llamar POST "/sesiones" @{ correo = $a; contrasena = "incorrecta123" }) 401

Mostrar "RF-03" "Guardar registro de hoy ($fHoy)" (Llamar PUT "/registros/$fHoy" @{ horas_trabajo = 5; tareas = 3; horas_sueno = 8; energia = 3 } $tokenA) 200
Mostrar "RF-03" "Guardar registro con fecha futura ($fFutura)" (Llamar PUT "/registros/$fFutura" $dia $tokenA) 400
Mostrar "RF-03" "Guardar registro de hace 7 días ($fVieja)" (Llamar PUT "/registros/$fVieja" $dia $tokenA) 400

Mostrar "RF-04" "6 h, 4 tareas, 7.5 h sueño, energía 4 (esperado 84)" (Llamar PUT "/registros/$fHoy" $dia $tokenA) 200 "calificación 84"

Mostrar "RNF-02" "PUT sin token" (Llamar PUT "/registros/$fHoy" $dia $null) 401
$c = $tokenA.ToCharArray(); $p = $c.Length - 5; $c[$p] = if ($c[$p] -eq "A") { "B" } else { "A" }
Mostrar "RNF-02" "PUT con token alterado" (Llamar PUT "/registros/$fHoy" $dia (-join $c)) 401

Llamar POST "/cuentas" @{ nombre = "Prueba B"; correo = $b; contrasena = $claveB } | Out-Null
$tokenB = (Llamar POST "/sesiones" @{ correo = $b; contrasena = $claveB }).json.token
$intruso = @{ usuario = $a; correo = $a; horas_trabajo = 0; tareas = 0; horas_sueno = 0; energia = 1 }
Mostrar "RNF-02" "Usuario B manda usuario=A en el cuerpo (se guarda como B)" (Llamar PUT "/registros/$fHoy" $intruso $tokenB) 200 "calificación 10"
Mostrar "RNF-02" "Usuario B intenta la ruta /registros/<correo A>:<fecha>" (Llamar PUT "/registros/${a}:$fHoy" $intruso $tokenB) 400

Remove-Item $tmp -ErrorAction SilentlyContinue
Write-Host ("`nResultado: {0} de {1} pruebas como se esperaba." -f $script:ok, $script:total) -ForegroundColor Cyan
Write-Host "Cuentas de prueba: $a y $b"
