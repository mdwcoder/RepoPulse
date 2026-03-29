# RepoPulse

RepoPulse es una aplicación desktop en Python + Flet para inspeccionar de forma visual la salud de un repositorio local. Está pensada como una companion app flotante para macOS y Linux: abre un repo, lo escanea y te enseña primero dónde mirar.

## Qué hace

- Abre una carpeta con selector nativo usando `FilePicker.get_directory_path()`
- Detecta si parece un repositorio Git y permite escanear una carpeta normal igualmente
- Calcula hotspots de archivos con heurísticas sin IA
- Resume el estado actual de Git
- Detecta heavy deletion desde `HEAD`
- Sugiere entradas potencialmente ausentes en `.gitignore`
- Permite refrescar el análisis con `Refresh Scan`
- Guarda settings, geometría de ventana y último repo abierto

## Stack

- Python 3.11+
- Flet
- `pathlib`
- `subprocess` para Git CLI
- JSON para settings y caché ligera

## Requisitos

- Python 3.11 o superior
- Git disponible en terminal
- macOS o Linux
- En Linux desktop, Flet necesita `zenity` para que el selector nativo de carpeta funcione

## Instalación

Desde la raíz del proyecto:

```bash
./init.sh
```

`init.sh` hace esto:

1. Detecta macOS o Linux
2. Comprueba Python 3.11+
3. Crea `.venv` si no existe
4. Instala dependencias desde `requirements.txt`
5. Crea un launcher ejecutable `repopulse`
6. Intenta instalarlo en `~/.local/bin/repopulse` y usa `~/bin/repopulse` si hace falta
7. Avisa si esa ruta no está en tu `PATH`

El script es idempotente. Puedes lanzarlo varias veces sin romper el entorno.

## Uso

Ejecución rápida local:

```bash
./run.sh
```

Si el launcher quedó en tu `PATH`:

```bash
repopulse
```

## Flujo principal

1. Abre RepoPulse
2. Pulsa `Open Repository`
3. Selecciona una carpeta con el explorador nativo
4. Si la carpeta contiene `.git`, se analiza como repositorio Git
5. Si no contiene `.git`, la app muestra:
   - `This folder does not look like a Git repository.`
   - opciones `Cancel` y `Scan folder anyway`
6. Navega por:
   - `Overview`
   - `Hotspots`
   - `Git`
   - `Ignore`
   - `Files`
7. Pulsa `Refresh Scan` para recalcular el estado

## Qué detecta

### Métricas por archivo

- line count
- size in bytes
- complejidad aproximada por tokens de control de flujo
- nesting máximo aproximado
- número aproximado de imports
- churn Git
- estado Git actual
- líneas añadidas y eliminadas
- preview corto del contenido

### Heurísticas estructurales

- Large file
- Huge function estimate
- Deep nesting
- Too many conditionals
- Too many imports

### Heurísticas de duplicación

- Possible duplication block
- Similar repeated fragments entre archivos

### Heurísticas Git

- High churn hotspot
- Many uncommitted changes
- Heavy deletion since last commit
- Many untracked files
- Generated files tracked

### Higiene de repositorio

- Suggested `.gitignore` entries
- Temporary/local file present
- Build/cache artifact detected

## Interfaz

La UI sigue una línea visual compacta y técnica:

- dark theme profundo
- cards densas y legibles
- colores de severidad claros
- listas rápidas de escanear
- panel lateral en modo ancho
- modal de detalle en modo estrecho

### Tabs

- `Overview`: score global, resumen, top hotspots y warnings recientes
- `Hotspots`: archivos prioritarios y detalle de cada archivo
- `Git`: cambios actuales, heavy deletion y commits recientes
- `Ignore`: sugerencias de `.gitignore`
- `Files`: inventario filtrable y ordenable de archivos

## Ventana desktop

RepoPulse usa la API desktop de Flet para:

- `page.window.width`
- `page.window.height`
- `page.window.left`
- `page.window.top`
- `page.window.always_on_top`
- `page.window.minimized`
- `page.window.minimizable`
- `page.window.resizable`
- `page.window.on_event`

Comportamiento:

- ventana redimensionable y minimizable
- pin de always-on-top
- restauración opcional de geometría
- usable en vertical estrecho y ancho
- anclaje inicial:
  - Linux: lado izquierdo
  - macOS: lado derecho

## Settings

Se guardan en JSON en el directorio de configuración del usuario:

- `remember window geometry`
- `restore last repo`
- `always on top default`
- `max preview lines`
- `ignore hidden files`
- `ignore binary files`
- `file size cap for preview`
- `scan ignored directories`
- thresholds de análisis

## Logging

Se registra actividad básica en:

- scans
- llamadas Git
- errores de lectura/ejecución

La ruta de configuración por defecto es:

```text
~/.config/repopulse/
```

## Estructura del proyecto

```text
repopulse/
  main.py
  init.sh
  run.sh
  requirements.txt
  README.md
  app/
    ui/
      main_window.py
      header.py
      overview_view.py
      hotspots_view.py
      git_view.py
      ignore_view.py
      files_view.py
      file_detail_panel.py
      settings_dialog.py
      theme.py
    controllers/
      app_controller.py
      scan_controller.py
      settings_controller.py
  core/
    models.py
    enums.py
    scanner.py
    analyzer.py
    git_service.py
    scoring.py
    duplication.py
    gitignore_checker.py
    preview.py
    window_service.py
    repository_validator.py
    utils/
      path_utils.py
      file_utils.py
      text_utils.py
      logger.py
      thresholds.py
  storage/
    settings_store.py
    cache_store.py
  assets/
    icon.png
```

## Limitaciones de esta V1

- No usa AST complejo ni análisis semántico profundo
- No interpreta arquitectura completa del proyecto
- La detección de duplicación es conservadora y aproximada
- El score de salud es heurístico, no “científico”
- No realiza acciones destructivas sobre Git
- No usa backend ni IA

## Nota para Linux

Para que el selector nativo de carpetas funcione correctamente en desktop con Flet, debes tener `zenity` disponible en el sistema.
