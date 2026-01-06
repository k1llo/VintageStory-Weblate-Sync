# Belarusian Translations Pack for Vintage Story

Community-maintained Belarusian translations for Vintage Story mods.

## Requirements

- .NET 10.0 SDK (or higher) - for full build pipeline with scripts
- .NET 8.0 SDK - only if building just the DLL without using the scripts
- `VINTAGE_STORY` environment variable pointing to game installation

```powershell
$env:VINTAGE_STORY = "C:\Program Files\Vintagestory"
```

## Building

```bash
# Test build (no history)
dotnet scripts/mods.cs -r linux-x64 -- build test-20260104 --no-history

# Release build
dotnet scripts/mods.cs -r linux-x64 -- build <version>

# Examples
dotnet scripts/mods.cs -r linux-x64 -- build 1.0.0
dotnet scripts/mods.cs -r linux-x64 -- build 1.2.0-pre.16
```

**Note:** The `-r linux-x64 --` flags are required on Linux systems (especially Fedora 43+).

## How It Works

The pack includes `TranslationReloader.dll` which:
1. Uses `ExecuteOrder() = double.MaxValue` to run last
2. Moves translation pack Origin to end of Origins list via reflection
3. Reloads all translations - our files load last and override older versions

## Weblate Integration

This repository is synchronized with **Weblate** for collaborative translation management:

- **Translation files** (`mods/*/assets/*/lang/be.json`) are edited directly on Weblate
- Translators contribute Belarusian translations via the Weblate web interface
- Weblate automatically commits translation changes back to this repository
- Each build includes the latest translations that were committed by Weblate
- **Supported mods** are defined in `mods.json` - this list determines which mods are tracked for translations

**Workflow:**
1. `dotnet scripts/mods.cs -r linux-x64 -- update` downloads mods from ModDB and extracts their `en.json` files (English strings)
2. Weblate detects new English strings and makes them available for translation
3. Translators edit Belarusian translations on Weblate
4. Weblate commits translation changes directly to this repository
5. `dotnet scripts/mods.cs -r linux-x64 -- build <version>` packages all `be.json` files with the mod pack

**Technical Detail:** The mod includes `TranslationReloader.dll` which ensures Belarusian translations override any older versions from mods by reordering asset origins and reloading translations after all mods have loaded.

## Commands

### Fix JSON formatting
```bash
dotnet scripts/mods.cs -r linux-x64 -- fix
```
Converts all JSON files in `mods/` folder to LF-only line endings and reformats them with 4-space indentation.

### Update mods from ModDB
```bash
dotnet scripts/mods.cs -r linux-x64 -- update
```
Downloads and extracts `en.json` files (English strings) from mods listed in `mods.json`. Only updates if new versions are detected. Creates/updates:
- `en.json` files extracted from mods (stored in `mods/<mod-name>/assets/*/lang/`)
- `mods.json` - Updates mod version numbers and last updated dates
- `update-log.txt` - Summary of updated mods (only created if changes detected)

Note: `be.json` files are NOT touched by this command - they must be translated separately via Weblate or manually.

### Build package
```bash
dotnet scripts/mods.cs -r linux-x64 -- build <version> [--no-history]
```

**Parameters:**
- `<version>` - Version string (e.g., `1.0.0`, `test-20260104`)
- `--no-history` - Skip saving to build history (optional, recommended for test builds)

Creates/updates:
- `BelarusianTranslationsPack_v<version>.zip` - Packaged mod with all translations
- `changelog_<version>.txt` - Detailed changelog
- `build-history.json` - Build history tracking (unless `--no-history` is used)

**Examples:**
```bash
# Test build
dotnet scripts/mods.cs -r linux-x64 -- build test-20260104 --no-history

# Release build
dotnet scripts/mods.cs -r linux-x64 -- build 1.0.0
```

## Configuration Files

### `translators.txt`
Contains the list of translator authors credited in the mod pack. Each name on a separate line.

**Used by:** `build` command - authors from this file are added to `modinfo.json` when packaging the mod. If the file doesn't exist or is empty, "Community Translators" is used as default.

**Example:**
```
alex_dev
marina
toma
```

### `mods.json`
Database of supported mods with their ModDB IDs, versions, and last update dates.

**Used by:** `update` command - determines which mods to download from ModDB.

**Format:**
```json
[
  {
    "name": "Mod Display Name",
    "modid": "moddb_id",
    "version": "1.2.3",
    "lastUpdated": "2025-11-20"
  }
]
```




