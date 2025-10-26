# Webhook Project

## 1. Instalación de UV

### Para macOS (usando Homebrew):
```bash
# Instalar Homebrew si no lo tienes
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar uv
brew install uv

# Verificar la instalación
uv --version
```

### Para Windows (usando PowerShell):
```powershell
# Instalar con winget (requiere winget instalado)
winget install uv

# O instalar manualmente descargando el instalador desde:
# https://github.com/astral-sh/uv/releases

# Verificar la instalación
uv --version
```

## 2. Creación de entorno virtual con UV

### Para macOS/Linux:
```bash
# Crear entorno virtual
uv venv

# Activar el entorno
source .venv/bin/activate
```

### Para Windows (PowerShell):
```powershell
# Crear entorno virtual
uv venv .venv

# Activar el entorno
.venv\Scripts\Activate.ps1
```

## 3. Instalación de dependencias

Asegúrate de tener un archivo `pyproject.toml` en la raíz de tu proyecto. Luego ejecuta:

```bash
# Instalar dependencias
uv pip install -e .

# O instalar dependencias de desarrollo también
uv pip install -e ".[dev]"

# O instalar dependencias de desarrollo también
uv sync
```

## 4. Estructura del Proyecto

```
webhook_pf/
├── .venv/                 # Entorno virtual de Python
├── src/                   # Código fuente principal
│   ├── __init__.py        # Paquete principal
│   └── webhook/           # Módulo de webhook
│       ├── __init__.py
│       ├── handlers.py    # Manejadores de webhook
│       └── models.py      # Modelos de datos
├── tests/                 # Pruebas unitarias
│   └── __init__.py
├── .gitignore             # Archivos ignorados por git
├── pyproject.toml         # Configuración del proyecto y dependencias
└── README.md              # Este archivo
```

### Descripción de archivos principales:

- `src/`: Contiene todo el código fuente de la aplicación.
- `tests/`: Pruebas unitarias y de integración.
- `pyproject.toml`: Configuración del proyecto, dependencias y metadatos.
- `.venv/`: Entorno virtual de Python (no se versiona).
- `.gitignore`: Especifica archivos y carpetas que git debe ignorar.

## Uso

1. Clona el repositorio
2. Crea y activa el entorno virtual
3. Instala las dependencias
4. Ejecuta la aplicación

```bash
# Ejemplo de ejecución
uvicorn main:app --port 8015 --workers 4
```