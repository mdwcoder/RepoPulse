[Español](README.es.md) | [English](README.en.md)

---

# RepoPulse

RepoPulse es una aplicacion de escritorio con Python y Flet para inspeccionar visualmente la salud de un repositorio local.

Esta disenada como una app flotante para macOS y Linux: abre un repositorio, escanea y muestra donde conviene mirar primero.

## Que hace

- Abre carpetas con el selector nativo.
- Detecta si la carpeta parece un repositorio Git.
- Calcula hotspots de archivos con heuristicas no IA.
- Resume el estado Git actual.
- Detecta eliminaciones grandes desde `HEAD`.
- Sugiere posibles entradas faltantes en `.gitignore`.
- Permite refrescar el analisis.
- Guarda configuracion, geometria de ventana y ultimo repositorio.

## Stack

- Python 3.11+
- Flet
- `pathlib`
- `subprocess` para Git CLI
- JSON para configuracion y cache ligera

## Requisitos

- Python 3.11 o superior.
- Git disponible en terminal.
- macOS o Linux.
- En Linux, Flet puede necesitar `zenity` para el selector nativo.

## Instalacion

```bash
./init.sh
```

El script crea `.venv`, instala dependencias y registra el lanzador `repopulse` cuando puede.

## Uso

```bash
./run.sh
# o, si esta en PATH
repopulse
```

## Flujo principal

1. Abre RepoPulse.
2. Pulsa `Open Repository`.
3. Selecciona una carpeta.
4. Revisa `Overview`, `Hotspots`, `Git`, `Ignore` y `Files`.
5. Pulsa `Refresh Scan` para recalcular.
