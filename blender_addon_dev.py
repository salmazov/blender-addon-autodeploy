#!/usr/bin/env python3
"""
Blender Add-on Development Tool

A script to package, install, and manage Blender add-ons during development.

Usage:
    blender-addon-dev --addon-name my_addon --addon-dir ./my_addon --install
    blender-addon-dev -n my_addon -d ./my_addon -i -l
"""

import os
import sys
import zipfile
import subprocess
import shutil
import argparse
import signal
import platform
import re
from pathlib import Path


def find_blender_executable():
    """Find Blender executable on the system"""
    # Common Blender paths
    possible_paths = [
        # macOS
        "/Applications/Blender.app/Contents/MacOS/Blender",
        # Linux (common locations)
        "/usr/bin/blender",
        "/usr/local/bin/blender",
        "~/.local/bin/blender",
        # Windows (if in PATH)
        "blender.exe",
        "blender",
    ]
    
    # Check if blender is in PATH
    blender_in_path = shutil.which("blender")
    if blender_in_path:
        return blender_in_path
    
    # Check common paths
    for path in possible_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            return expanded_path
    
    return None


def detect_addon_name_from_bl_info(addon_dir):
    """Try to detect add-on name from bl_info in __init__.py"""
    init_file = Path(addon_dir) / "__init__.py"
    if not init_file.exists():
        return None
    
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to find bl_info dictionary
        # Look for patterns like: bl_info = {...} or bl_info = dict(...)
        bl_info_match = re.search(r'bl_info\s*=\s*\{([^}]+)\}', content, re.DOTALL)
        if bl_info_match:
            bl_info_content = bl_info_match.group(1)
            # Try to find 'name' key
            name_match = re.search(r"['\"]name['\"]\s*:\s*['\"]([^'\"]+)['\"]", bl_info_content)
            if name_match:
                # Convert name to module name (lowercase, replace spaces with underscores)
                name = name_match.group(1)
                module_name = name.lower().replace(' ', '_').replace('-', '_')
                return module_name
        
        # Fallback: use directory name
        return Path(addon_dir).name
    except Exception:
        return None


def auto_detect_addon_dir():
    """Auto-detect add-on directory"""
    current_dir = Path.cwd()
    
    # Check if current directory is an add-on (has __init__.py with bl_info)
    if (current_dir / "__init__.py").exists():
        try:
            with open(current_dir / "__init__.py", 'r', encoding='utf-8') as f:
                if 'bl_info' in f.read():
                    return current_dir
        except Exception:
            pass
    
    # Check for subdirectories with __init__.py
    addon_dirs = []
    for item in current_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            if (item / "__init__.py").exists():
                try:
                    with open(item / "__init__.py", 'r', encoding='utf-8') as f:
                        if 'bl_info' in f.read():
                            addon_dirs.append(item)
                except Exception:
                    pass
    
    if len(addon_dirs) == 1:
        return addon_dirs[0]
    elif len(addon_dirs) > 1:
        print("Multiple add-on directories found. Please specify --addon-dir")
        return None
    
    return None


def create_addon_zip(addon_dir, addon_name, output_zip=None):
    """Create a ZIP file of the add-on for Blender installation."""
    addon_dir = Path(addon_dir)
    
    if not addon_dir.exists():
        print(f"Error: Add-on directory not found: {addon_dir}")
        return None
    
    if not (addon_dir / "__init__.py").exists():
        print(f"Error: __init__.py not found in {addon_dir}")
        return None
    
    # Determine output ZIP path
    if output_zip is None:
        output_zip = addon_dir.parent / f"{addon_name}.zip"
    else:
        output_zip = Path(output_zip)
    
    print(f"Packaging add-on from: {addon_dir}")
    print(f"Output ZIP: {output_zip}")
    
    # Remove existing ZIP if it exists
    if output_zip.exists():
        output_zip.unlink()
        print("Removed existing ZIP file")
    
    # Create ZIP file
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the addon directory
        for root, dirs, files in os.walk(addon_dir):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
            
            for file in files:
                # Skip excluded files
                if any(file.endswith(ext) for ext in ['.pyc', '.pyo', '.DS_Store']):
                    continue
                
                file_path = Path(root) / file
                # Create archive path relative to addon_dir
                arcname = file_path.relative_to(addon_dir.parent)
                zipf.write(file_path, arcname)
                print(f"  Added: {arcname}")
    
    print(f"\n✓ Successfully created: {output_zip}")
    
    return output_zip


def kill_blender_processes():
    """Kill all running Blender processes"""
    print("\n" + "="*60)
    print("Killing Blender processes...")
    print("="*60)
    
    system = platform.system()
    killed_count = 0
    
    try:
        if system == "Darwin":  # macOS
            # Find Blender processes
            result = subprocess.run(
                ["pgrep", "-f", "Blender"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                            print(f"  ✓ Killed Blender process {pid}")
                            killed_count += 1
                        except ProcessLookupError:
                            pass  # Process already dead
                        except Exception as e:
                            print(f"  Warning: Could not kill process {pid}: {e}")
            
            # Also try pkill
            subprocess.run(["pkill", "-f", "Blender"], 
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)
            
        elif system == "Linux":
            # Find Blender processes
            result = subprocess.run(
                ["pgrep", "-f", "blender"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                            print(f"  ✓ Killed Blender process {pid}")
                            killed_count += 1
                        except ProcessLookupError:
                            pass
                        except Exception as e:
                            print(f"  Warning: Could not kill process {pid}: {e}")
            
            subprocess.run(["pkill", "-f", "blender"],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)
            
        elif system == "Windows":
            # Windows: use taskkill
            subprocess.run(
                ["taskkill", "/F", "/IM", "blender.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            killed_count = 1  # taskkill doesn't give us a count easily
        
        if killed_count > 0:
            print(f"\n✓ Killed {killed_count} Blender process(es)")
            # Wait a moment for processes to fully terminate
            import time
            time.sleep(1)
        else:
            print("  No Blender processes found running")
        
        return True
        
    except Exception as e:
        print(f"  Warning: Error killing Blender processes: {e}")
        return False


def uninstall_addon(blender_exe, addon_name):
    """Uninstall the addon using Blender"""
    print("\n" + "="*60)
    print("Step 1: Uninstalling existing add-on...")
    print("="*60)
    
    uninstall_script = f'''
import bpy
import os
import shutil

addon_name = "{addon_name}"

print("Uninstalling add-on:", addon_name)

# Disable if enabled
try:
    enabled_addons = [addon.module for addon in bpy.context.preferences.addons]
    if addon_name in enabled_addons:
        bpy.ops.preferences.addon_disable(module=addon_name)
        print("  ✓ Disabled")
except Exception as e:
    print(f"  Warning disabling: {{e}}")

# Remove if installed
try:
    import addon_utils
    available_addons = [mod.__name__ for mod in addon_utils.modules()]
    if addon_name in available_addons:
        try:
            # Try to remove using operator (may fail in background mode due to context.area)
            bpy.ops.preferences.addon_remove(module=addon_name)
            print("  ✓ Removed using operator")
        except (AttributeError, RuntimeError) as e:
            # AttributeError: context.area is None in background mode
            # RuntimeError: other operator errors
            # Fall back to filesystem removal
            print(f"  Operator remove failed (expected in background mode), trying filesystem...")
            try:
                addons_dir = bpy.utils.user_resource('SCRIPTS', path="addons")
                addon_path = os.path.join(addons_dir, addon_name)
                if os.path.exists(addon_path):
                    shutil.rmtree(addon_path)
                    print(f"  ✓ Removed from filesystem")
                else:
                    print("  Add-on not found in filesystem")
            except Exception as e2:
                print(f"  Filesystem removal also failed: {{e2}}")
        except Exception as e:
            print(f"  Unexpected error during remove: {{e}}")
    else:
        print("  Add-on not installed")
except Exception as e:
    print(f"  Error checking installed addons: {{e}}")

# Save preferences
try:
    bpy.ops.wm.save_userpref()
    print("  ✓ Preferences saved")
except:
    pass

print("\\n✓ Uninstall complete")
'''
    
    try:
        result = subprocess.run(
            [blender_exe, "--background", "--python-expr", uninstall_script],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            print("✓ Uninstall completed")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print("⚠ Uninstall had warnings (this is usually OK)")
            if result.stdout:
                print(result.stdout)
            return True  # Continue even if there are warnings
            
    except Exception as e:
        print(f"⚠ Uninstall error (may not be installed): {e}")
        return True  # Continue anyway


def install_startup_script(blender_exe, addon_name):
    """Install startup script to auto-enable the add-on"""
    print("\n" + "="*60)
    print("Step 4: Installing startup script...")
    print("="*60)
    
    # Startup script content template
    startup_script_content = f'''"""
Blender startup script to auto-enable {addon_name} add-on
This script is automatically installed by blender-addon-dev
"""

import bpy
import addon_utils

def auto_enable_addon():
    """Auto-enable {addon_name} add-on if it's installed but not enabled"""
    addon_name = "{addon_name}"
    
    try:
        # Check if addon is already enabled
        enabled_addons = [addon.module for addon in bpy.context.preferences.addons]
        if addon_name in enabled_addons:
            return  # Already enabled, nothing to do
        
        # Check if it's available but not enabled
        available_addons = [mod.__name__ for mod in addon_utils.modules()]
        if addon_name in available_addons:
            try:
                # Enable with persistent flag
                addon_utils.enable(addon_name, default_set=True, persistent=True)
                print(f"{{addon_name}}: Auto-enabled {{addon_name}}")
                # Save preferences to make it stick
                try:
                    bpy.ops.wm.save_userpref()
                except:
                    pass
            except Exception as e:
                print(f"{{addon_name}}: Could not auto-enable: {{e}}")
        # If not found, silently skip (add-on not installed yet)
    except Exception as e:
        # Silently fail to avoid cluttering console
        pass

# Register to run after Blender loads
def on_load_post(dummy):
    auto_enable_addon()

# Register the handler
if hasattr(bpy.app.handlers, 'load_post'):
    bpy.app.handlers.load_post.append(on_load_post)

# Also run immediately if we're already loaded
try:
    auto_enable_addon()
except:
    pass
'''
    
    # Escape the script content for embedding in f-string
    escaped_content = startup_script_content.replace('{', '{{').replace('}', '}}')
    
    # Create installation script to copy startup script
    install_script = f'''
import bpy
import os

startup_script_content = """{escaped_content}"""

# Get scripts directory
scripts_dir = bpy.utils.user_resource('SCRIPTS')
startup_dir = os.path.join(scripts_dir, "startup")

# Create startup directory if it doesn't exist
os.makedirs(startup_dir, exist_ok=True)

# Write startup script
startup_script_path = os.path.join(startup_dir, "{addon_name}_auto_enable.py")
try:
    with open(startup_script_path, 'w') as f:
        f.write(startup_script_content)
    print(f"  ✓ Startup script installed: {{startup_script_path}}")
except Exception as e:
    print(f"  ⚠ Could not install startup script: {{e}}")
'''
    
    try:
        result = subprocess.run(
            [blender_exe, "--background", "--python-expr", install_script],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print("  ⚠ Startup script installation had warnings")
            if result.stdout:
                print(result.stdout)
            return True  # Continue anyway
    except Exception as e:
        print(f"  ⚠ Could not install startup script: {e}")
        return True  # Continue anyway


def auto_install_to_blender(zip_path, addon_name, launch_blender=False):
    """Auto-install the packaged addon to Blender"""
    print("\n" + "="*60)
    print("Auto-installing to Blender...")
    print("="*60)
    
    blender_exe = find_blender_executable()
    
    if not blender_exe:
        print("\n❌ Blender executable not found!")
        print("\nPlease install manually:")
        print("  1. Open Blender")
        print("  2. Go to Edit > Preferences > Add-ons")
        print("  3. Click 'Install...'")
        print(f"  4. Select: {zip_path}")
        print("  5. Enable the add-on in the list")
        return False
    
    print(f"Found Blender at: {blender_exe}")
    
    # Step 1: Kill any running Blender processes
    kill_blender_processes()
    
    # Step 2: Uninstall existing addon
    uninstall_addon(blender_exe, addon_name)
    
    # Step 3: Install new version
    print("\n" + "="*60)
    print("Step 3: Installing new add-on...")
    print("="*60)
    
    # Create installation script
    zip_abs_path = os.path.abspath(zip_path)
    install_script = f'''
import bpy
import os

zip_path = r"{zip_abs_path}"
addon_name = "{addon_name}"

if not os.path.exists(zip_path):
    print(f"Error: ZIP file not found: {{zip_path}}")
    exit(1)

print("Installing add-on from:", zip_path)

# Install new version
try:
    bpy.ops.preferences.addon_install(filepath=zip_path)
    print("  ✓ Add-on installed successfully")
except Exception as e:
    print(f"  ❌ Error installing: {{e}}")
    import traceback
    traceback.print_exc()
    exit(1)

# Enable the add-on using addon_utils (more reliable)
try:
    import addon_utils
    # Enable with persistent flag to ensure it stays enabled
    addon_utils.enable("{addon_name}", default_set=True, persistent=True)
    print("  ✓ Add-on enabled using addon_utils (persistent)")
except Exception as e:
    print(f"  Warning: addon_utils enable failed: {{e}}")

# Save preferences to make it persistent
try:
    bpy.ops.wm.save_userpref()
    print("  ✓ Preferences saved")
except Exception as e:
    print(f"  Warning: Could not save preferences: {{e}}")

# Verify it's enabled
try:
    enabled_addons = [addon.module for addon in bpy.context.preferences.addons]
    if "{addon_name}" in enabled_addons:
        print("\\n✓ {addon_name} add-on installed and enabled!")
    else:
        print("\\n⚠ Add-on installed but not in enabled list. This may be normal in background mode.")
        print("  The add-on should be enabled when you open Blender.")
except Exception as e:
    print(f"\\n⚠ Could not verify enable status: {{e}}")
    print("  The add-on should be enabled when you open Blender.")
'''
    
    try:
        # Run Blender in background mode with the install script
        print("Running Blender to install add-on...")
        result = subprocess.run(
            [blender_exe, "--background", "--python-expr", install_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"\n✓ Successfully installed and enabled {addon_name} add-on!")
            
            # Step 4: Install startup script
            install_startup_script(blender_exe, addon_name)
            
            # Step 5: Launch Blender if requested
            if launch_blender:
                print("\n" + "="*60)
                print("Step 5: Launching Blender...")
                print("="*60)
                try:
                    # Launch Blender in foreground
                    if platform.system() == "Darwin":  # macOS
                        # Use open command to launch app properly
                        subprocess.Popen(["open", "-a", "Blender"])
                    else:
                        # Linux/Windows: launch directly
                        subprocess.Popen([blender_exe])
                    print("✓ Blender launched!")
                except Exception as e:
                    print(f"⚠ Could not launch Blender: {e}")
                    print("Please open Blender manually")
            else:
                print("\nYou can now open Blender and use the add-on.")
            
            return True
        else:
            print("\n❌ Installation failed!")
            print("Blender output:")
            print(result.stdout)
            if result.stderr:
                print("Errors:")
                print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("\n❌ Installation timed out")
        return False
    except Exception as e:
        print(f"\n❌ Error running Blender: {e}")
        return False


def main():
    """Main function with command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Generic Blender Add-on Development Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect add-on directory and name
  blender-addon-dev --install
  
  # Specify add-on name and directory
  blender-addon-dev --addon-name my_addon --addon-dir ./my_addon --install
  
  # Short form with launch
  blender-addon-dev -n my_addon -d ./src -i -l
  
  # Just package (no install)
  blender-addon-dev -n my_addon -d ./my_addon
        """
    )
    parser.add_argument(
        '-n', '--addon-name',
        type=str,
        help='Add-on module name (e.g., my_addon). If not provided, will try to detect from bl_info.'
    )
    parser.add_argument(
        '-d', '--addon-dir',
        type=str,
        help='Path to add-on directory. If not provided, will try to auto-detect.'
    )
    parser.add_argument(
        '-i', '--install',
        action='store_true',
        help='Auto-install the addon to Blender after packaging'
    )
    parser.add_argument(
        '-l', '--launch',
        action='store_true',
        help='Launch Blender after installation (requires --install)'
    )
    
    args = parser.parse_args()
    
    # Auto-detect addon directory if not provided
    addon_dir = args.addon_dir
    if addon_dir is None:
        print("Auto-detecting add-on directory...")
        addon_dir = auto_detect_addon_dir()
        if addon_dir is None:
            print("❌ Could not auto-detect add-on directory.")
            print("Please specify --addon-dir or ensure you're in an add-on directory.")
            return 1
        print(f"  Found: {addon_dir}")
    else:
        addon_dir = Path(args.addon_dir)
        if not addon_dir.exists():
            print(f"❌ Add-on directory not found: {addon_dir}")
            return 1
    
    # Auto-detect addon name if not provided
    addon_name = args.addon_name
    if addon_name is None:
        print("Auto-detecting add-on name...")
        addon_name = detect_addon_name_from_bl_info(addon_dir)
        if addon_name is None:
            # Fallback to directory name
            addon_name = Path(addon_dir).name
        print(f"  Using: {addon_name}")
    
    # Package the addon
    print("="*60)
    print(f"Packaging Blender Add-on: {addon_name}")
    print("="*60)
    
    zip_path = create_addon_zip(addon_dir, addon_name)
    
    if not zip_path:
        print("\n❌ Packaging failed!")
        return 1
    
    # Auto-install if requested
    if args.install:
        launch = args.launch
        success = auto_install_to_blender(zip_path, addon_name, launch_blender=launch)
        return 0 if success else 1
    else:
        print(f"\nTo install manually:")
        print(f"  1. Open Blender")
        print(f"  2. Go to Edit > Preferences > Add-ons")
        print(f"  3. Click 'Install...'")
        print(f"  4. Select: {zip_path}")
        print(f"  5. Enable the add-on in the list")
        print(f"\nOr use --install flag to auto-install:")
        print(f"  blender-addon-dev -n {addon_name} -d {addon_dir} --install")
        return 0


if __name__ == "__main__":
    exit(main())

