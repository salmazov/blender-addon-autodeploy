# Blender Add-on Dev Tool

A generic development tool for Blender add-ons that automates packaging, installation, and management during development.

## Features

- **Package add-ons** into ZIP files for Blender installation
- **Auto-install** add-ons to Blender
- **Auto-enable** add-ons on Blender startup
- **Kill running Blender** processes before installation
- **Uninstall old versions** before installing new ones
- **Auto-detect** add-on directory and name from `bl_info`
- **Launch Blender** after installation

## Installation

1. Clone or download this repository
2. Make the script executable (optional):
   ```bash
   chmod +x blender_addon_dev.py
   ```

## Usage

### Basic Usage

```bash
# Auto-detect add-on directory and name, then install
blender-addon-dev --install

# Specify add-on name and directory
blender-addon-dev --addon-name my_addon --addon-dir ./my_addon --install

# Short form
blender-addon-dev -n my_addon -d ./my_addon -i

# Install and launch Blender
blender-addon-dev -n my_addon -d ./my_addon -i -l
```

### Command-Line Arguments

- `-n, --addon-name`: Add-on module name (e.g., `my_addon`)
  - If not provided, will try to detect from `bl_info` in `__init__.py`
  - Falls back to directory name if detection fails

- `-d, --addon-dir`: Path to add-on directory
  - If not provided, will auto-detect:
    - Checks if current directory contains `__init__.py` with `bl_info`
    - Checks for single subdirectory with `__init__.py` and `bl_info`
  - If multiple add-ons found, you must specify this argument

- `-i, --install`: Auto-install the add-on to Blender after packaging
  - Kills running Blender processes
  - Uninstalls existing version
  - Installs new version
  - Enables the add-on
  - Installs startup script for auto-enable

- `-l, --launch`: Launch Blender after installation (requires `--install`)

### Examples

#### Example 1: Add-on in Current Directory

If your add-on is in the current directory:

```bash
cd /path/to/my_addon
blender-addon-dev --install
```

The tool will:
1. Detect the current directory as the add-on directory
2. Extract the add-on name from `bl_info` or use the directory name
3. Package, install, and enable the add-on

#### Example 2: Add-on in Subdirectory

If your add-on is in a subdirectory:

```bash
cd /path/to/my_project
blender-addon-dev -n my_addon -d ./src/my_addon -i
```

#### Example 3: Just Package (No Install)

To just create the ZIP file without installing:

```bash
blender-addon-dev -n my_addon -d ./my_addon
```

The ZIP file will be created in the parent directory of the add-on.

#### Example 4: Full Workflow

Complete development workflow:

```bash
blender-addon-dev -n my_addon -d ./my_addon -i -l
```

This will:
1. Package the add-on
2. Kill any running Blender instances
3. Uninstall the old version
4. Install the new version
5. Enable the add-on
6. Install startup script for auto-enable
7. Launch Blender

## How It Works

### Auto-Detection

The tool tries to automatically detect:

1. **Add-on Directory**:
   - Checks if current directory has `__init__.py` with `bl_info`
   - Checks for single subdirectory with `__init__.py` and `bl_info`
   - If multiple found, requires manual specification

2. **Add-on Name**:
   - Reads `bl_info['name']` from `__init__.py`
   - Converts to module name (lowercase, spaces/ hyphens to underscores)
   - Falls back to directory name

### Installation Process

When using `--install`, the tool:

1. **Kills Blender processes** - Ensures clean installation
2. **Uninstalls old version** - Removes existing add-on if present
3. **Installs new version** - Installs from ZIP file
4. **Enables add-on** - Enables with persistent flag
5. **Installs startup script** - Creates script to auto-enable on Blender startup
6. **Launches Blender** (if `--launch` specified)

### Startup Script

The tool automatically installs a startup script in Blender's startup directory:
- **macOS**: `~/Library/Application Support/Blender/5.0/scripts/startup/`
- **Linux**: `~/.config/blender/5.0/scripts/startup/`
- **Windows**: `%APPDATA%\Blender Foundation\Blender\5.0\scripts\startup\`

The startup script ensures your add-on is automatically enabled every time Blender starts.

## Requirements

- Python 3.6+
- Blender installed on your system
- Blender executable in PATH or standard installation location

## Troubleshooting

### "Blender executable not found"

The tool looks for Blender in:
- System PATH
- Standard installation locations:
  - macOS: `/Applications/Blender.app/Contents/MacOS/Blender`
  - Linux: `/usr/bin/blender`, `/usr/local/bin/blender`, `~/.local/bin/blender`
  - Windows: `blender.exe` in PATH

If Blender is installed elsewhere, add it to your PATH or create a symlink.

### "Could not auto-detect add-on directory"

Make sure:
- You're in the add-on directory, or
- There's a single subdirectory with `__init__.py` containing `bl_info`, or
- Specify `--addon-dir` manually

### "Could not auto-detect add-on name"

The tool looks for `bl_info['name']` in `__init__.py`. If not found, it uses the directory name. You can always specify `--addon-name` manually.

### Add-on not enabling automatically

Check:
- The startup script was installed (check Blender's startup directory)
- Blender preferences are saved
- The add-on name matches exactly (case-sensitive)

### Installation fails in background mode

Some errors in background mode are expected (like `context.area` being None). The tool handles these gracefully and falls back to filesystem operations.

## License

This tool is provided as-is for Blender add-on development. Feel free to use and modify as needed.

## Contributing

This is a standalone tool. If you find issues or want to improve it, feel free to fork and modify for your needs.

## Author

Sergei Almazov
