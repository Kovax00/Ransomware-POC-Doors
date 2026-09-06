# RANS0M (Python) — Ransomware POC

POC de ransomware en Python, port del proyecto C# **RANS0M**
(https://github.com/Ixars/ransomdoors, recreación fan de la entidad RANSOM/A-90
de *Doors*, Roblox), convertido en una prueba de concepto con cifrado real.

## Uso

```
py main.py                              # cifra la carpeta predeterminada (prueba/)
py main.py --cifrado "C:\mi\carpeta"    # cifra esa carpeta (recursivo, hacia abajo)
```

Secuencia: ataque visual → **cifrado completo** del árbol → recién entonces
abre la ventana de rescate (con música en bucle y contador de 24h). El
**identificador** anti re-cifrado es doble: extensión `.rans0m` + cabecera
`RANS0M1` dentro del archivo — un archivo ya cifrado nunca se cifra dos veces
(aunque se ejecute el POC otra vez sobre la misma carpeta).

## Comportamiento (POC)

1. Al arrancar: **un solo ataque** — cara glitch animada → señal de stop a
   pantalla completa → cara grande sobre fondo rojo → jumpscare 900x900 con
   temblor → pantalla "DOWNLOADING..." falsa → flash rojo.
2. **"Infección"**: se esconden **5 monedas** (`moneda_1.gold` a `moneda_5.gold`
   — 2 en Descargas, 1 en Imágenes, 2 en Vídeos, con rutas reales de Windows) y
   se **cifra** todo el árbol de `TARGET_PATH` (recursivo, sólo hacia abajo) con
   **ChaCha20-Poly1305**. La clave de cada archivo viaja envuelta con
   **RSA-OAEP-2048** usando la **clave pública hardcodeada** en
   `ransom_crypto.py` — sin la privada, no hay descifrado posible.
3. Ventana de rescate con **cuenta atrás de 24 horas** y música en bucle.
4. **Pago**: las 5 monedas escondidas contienen 5 partes XOR de la clave
   privada. Arrastrar **las 5** a la ventana reconstruye la clave, descifra
   automáticamente todo y cancela el apagado. Menos de 5 (o copias) no sirve.
5. Si el plazo expira sin las 5 monedas → **`shutdown /s /t 0`** con los
   archivos aún cifrados.

Las monedas están cifradas con DPAPI (sólo el usuario actual puede abrirlas).
Las monedas de formato antiguo (`RANSOM_COIN`) se ignoran.

## Red de seguridad del equipo de pruebas

- `private_key.pem` — clave privada RSA completa (no forma parte del "ataque";
  no la pierdas si quieres poder descifrar sin las monedas).
- `decrypt_tool.py` — descifra un árbol con la clave privada:
  `python decrypt_tool.py [ruta]`.
- Escaparate de emergencia durante un rescate activo: matar `python.exe` desde
  el Administrador de tareas (la bandeja está bloqueada, como el original).
- `RANSOM_DURATION` y `TARGET_PATH` se ajustan en `global_state.py`.

## Cambios respecto al original C#

1. **BSOD eliminado** — siempre `shutdown /s /t 0` normal.
2. **Un solo ataque** (sin loop aleatorio) y **esquiva eliminada** (sin hook de
   teclado): el rescate siempre se desencadena.
3. **Cifrado real** ChaCha20-Poly1305 + RSA (el original sólo simulaba).
4. **Monedas como clave**: ahora contienen las 5 partes de la clave privada.
5. **Plazo de pago: 24 horas** con contador `TIME: HH:MM:SS`.

## Requisitos

- Windows
- Python 3.10+ (`py -3`)

```
py -3 -m pip install -r requirements.txt
py main.py
```

Dependencias: `cryptography` (ChaCha20-Poly1305 + RSA), `Pillow`, `pystray`,
`tkinterdnd2`.

## Estructura

| Archivo | Equivalente C# / función |
|---|---|
| `main.py` | `Program.cs` |
| `global_state.py` | `Global.cs` + configuración (`RANSOM_DURATION`, `TARGET_PATH`) |
| `ransom_crypto.py` | *(nuevo)* ChaCha20-Poly1305 streaming + RSA-OAEP + shares XOR |
| `ransomware_encryptor.py` | *(nuevo)* walker descendente optimizado (scandir + hilos) |
| `poc_coins.py` | `GoldCoinManager.cs` (DPAPI + registro, ahora con partes de clave) |
| `decrypt_tool.py` | *(nuevo)* rescate con `private_key.pem` |
| `sound_helper.py` | `SoundHelper.cs` (MCI/winmm, OST en bucle) |
| `overlay.py` | `Overlay.cs` |
| `ransomed_window.py` | `Ransomed.cs` |
| `taunt_window.py` | `TauntWindow.cs` |
| `thank_you_window.py` | `ThankYou.cs` |
| `winutil.py` | utilidades Win32 (`ControlBox = false`) |
| `keyboard_hook.py` | *(eliminado: la esquiva ya no existe)* |

## Solución de problemas

- **No aparece nada al ejecutarlo**: intérprete equivocado (stub de la Store u
  otro Python sin dependencias). Usa `py main.py`.
- **Errores de arranque**: cuadro de diálogo con traceback + `errors.log`.
- **Errores en caliente**: quedan en `errors.log` sin matar la app.

## Créditos

- *Doors* es obra de **LSPLASH**; RANSOM/A-90 es su creación. Proyecto fan no
  oficial.
- Sonidos e imágenes del juego, sacados de las wikis (mismo paquete de recursos
  que el original).
