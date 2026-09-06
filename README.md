# RANS0M — POC de ransomware (Python)
<img width="1919" height="884" alt="image" src="https://github.com/user-attachments/assets/4fd80294-45f4-4fee-998b-a5657398e37d" />

Prueba de concepto de ransomware para Windows construida sobre el port del
proyecto C# **RANS0M** (https://github.com/Ixars/ransomdoors, recreación fan de
la entidad RANSOM/A-90 de *Doors*, Roblox). Cifra de verdad (ChaCha20-Poly1305
+ RSA-OAEP), exige un rescate simbólico y apaga el equipo si no se paga.

---

## ⚠️ ADVERTENCIA — LÉELO ANTES DE EJECUTAR

**Este software es una prueba de concepto con efectos reales y destructivos.**
No es una simulación ni un juego.

- **Cifra archivos reales de forma irreversible** para cualquier persona que no
  posea la clave privada. Si pierdes `private_key.pem` y las 5 monedas, no hay
  forma de recuperarlos.
- **Apaga el equipo** de forma inmediata si el plazo de 24 horas expira sin
  pago. Guarda todo tu trabajo antes de ejecutarlo.
- Utiliza técnicas empleadas por malware real (cifrado híbrido, ocultación de
  material de clave, bloqueo de salidas). Los antivirus pueden detectarlo y
  bloquearlo: es el comportamiento esperado.

Al ejecutarlo aceptas que:

1. Lo haces **exclusivamente en equipos de tu propiedad o con autorización
   expresa por escrito** del responsable del equipo, con fines educativos o de
   investigación en seguridad.
2. Eres el **único responsable** de cualquier pérdida de datos, tiempo de
   inactividad, infracción de políticas o daños derivados de su uso.
3. **No lo usarás** contra terceros, equipos ajenos, entornos de producción ni
   con ningún fin ilícito. Distribuir o usar herramientas de este tipo contra
   sistemas sin autorización es un delito en la mayoría de jurisdicciones.
4. Los autores y colaboradores de este repositorio **no se hacen responsables**
   del mal uso del software.

Si no aceptas estas condiciones, **no ejecutes este programa**.

---

## Uso

```
py main.py                              # cifra la carpeta predeterminada (prueba/)
py main.py --cifrado "C:\mi\carpeta"    # cifra esa carpeta (recursivo, hacia abajo)
```

Secuencia: cifrado silencioso del árbol objetivo → ataque visual (cara
glitch, señal de stop, jumpscare, pantalla de descarga) → ventana de rescate
con contador de **24 horas** y música en bucle.

**Rescate**: esconde las 5 monedas (2 en Descargas, 1 en Imágenes, 2 en
Vídeos). Arrastra **las 5** a la ventana: cada una contiene una parte de la
clave privada; al reunirlas se descifra todo automáticamente con barra de
progreso y el script termina.

**Identificador anti re-cifrado**: los archivos cifrados quedan como
`*.rans0m` con cabecera `RANS0M1`. Un archivo ya cifrado nunca se cifra dos
veces, aunque vuelvas a ejecutar el POC sobre la misma carpeta.

## Comportamiento (POC)

1. Al arrancar: **cifrado silencioso** de todo el árbol de `TARGET_PATH`
   (recursivo, sólo hacia abajo) con **ChaCha20-Poly1305**. La clave de cada
   archivo viaja envuelta con **RSA-OAEP-2048** usando la **clave pública
   hardcodeada** en `ransom_crypto.py`.
2. Se esconden **5 monedas** (`moneda_1.gold` a `moneda_5.gold` — 2 en
   Descargas, 1 en Imágenes, 2 en Vídeos). Cada moneda lleva cifrada con
   DPAPI una parte XOR de la clave privada RSA.
3. Ataque visual: cara glitch animada → señal de stop a pantalla completa →
   cara grande sobre fondo rojo → jumpscare 900x900 con temblor → pantalla
   "DOWNLOADING..." falsa → flash rojo.
4. Ventana de rescate con contador de 24 horas y música en bucle. La bandeja
   queda bloqueada durante el rescate.
5. Pago con las 5 monedas → descifrado automático con barra de progreso →
   el script termina. Plazo expirado sin pago → **`shutdown /s /t 0`** con los
   archivos aún cifrados.

## Red de seguridad del equipo de pruebas

- `private_key.pem` — clave privada RSA completa. **Cópiala a un lugar seguro
  antes de ejecutar el POC**: sin ella (o sin las 5 monedas) los archivos no
  se recuperan.
- `decrypt_tool.py` — descifra un árbol con la clave privada:
  ```
  py decrypt_tool.py [ruta]
  ```
- Escapa de emergencia durante un rescate activo: termina el proceso
  `python.exe` desde el Administrador de tareas (la bandeja está bloqueada).
- `RANSOM_DURATION` (plazo) y `TARGET_PATH` (ruta por defecto) se ajustan en
  `global_state.py`.

## Requisitos

- Windows
- Python 3.10+ (`py -3`)

```
py -3 -m pip install -r requirements.txt
```

Dependencias: `cryptography` (ChaCha20-Poly1305 + RSA), `Pillow`, `pystray`,
`tkinterdnd2`.

## Solución de problemas

- **No aparece nada al ejecutarlo**: intérprete equivocado (stub de la Store u
  otro Python sin dependencias). Usa `py main.py`.
- **Errores de arranque**: cuadro de diálogo con traceback completo, y quedan
  registrados en `errors.log`.
- **Errores en caliente**: quedan en `errors.log` sin interrumpir la ejecución.
- **Quedan archivos `.rans0m`**: recupéralos con `decrypt_tool.py` o arrastrando
  las 5 monedas al rescate antes del plazo.

## Estructura

| Archivo | Función |
|---|---|
| `main.py` | punto de entrada; cifrado silencioso previo + arranque |
| `global_state.py` | configuración (`RANSOM_DURATION`, `TARGET_PATH`) y estado |
| `ransom_crypto.py` | ChaCha20-Poly1305 por chunks + envoltura RSA-OAEP + shares XOR |
| `ransomware_encryptor.py` | recorrido descendente del árbol y cifrado/descifrado en paralelo |
| `poc_coins.py` | las 5 monedas (DPAPI + registro) con partes de la clave privada |
| `decrypt_tool.py` | herramienta de rescate con la clave privada |
| `overlay.py` | overlay transparente a pantalla completa y fases del rescate |
| `ransomed_window.py` | ventana de rescate, contador y barra de descifrado |
| `taunt_window.py` | ventanas de provocación |
| `sound_helper.py` | reproducción de audio vía MCI/winmm (OST en bucle) |
| `winutil.py` | utilidades Win32 (ocultar botones de la ventana) |
| `resources.py` | carga de imágenes y sonidos del juego |
| `resources/` | imágenes, sonidos e iconos |

## Créditos

- *Doors* es obra de **LSPLASH**; RANSOM/A-90 es su creación. Proyecto fan no
  oficial.
- Sonidos e imágenes del juego, tomados de las wikis de la comunidad.
