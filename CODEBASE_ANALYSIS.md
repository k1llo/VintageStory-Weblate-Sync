# Vintage Story Polish Translations Pack - Complete Codebase Analysis

**Date:** 2026-01-01  
**Purpose:** Comprehensive understanding document for AI assistant

---

## PROJECT OVERVIEW

**Name:** Vintage Story Polish Translations Pack (VintageStory-Weblate-Sync)  
**Purpose:** Community-maintained Polish translation mod for Vintage Story game and its mods  
**Integration:** Weblate-based collaborative translation platform  
**Output:** Packaged mod (.zip) containing Polish translations that override mod translations

---

## ARCHITECTURE

### Core Workflow
```
1. MOD UPDATE PHASE
   └─> scripts/mods.cs update
       └─> Fetches mods from ModDB API
       └─> Downloads mod zip files
       └─> Extracts en.json (English source)
       └─> Saves to mods/<mod-name>/assets/*/lang/en.json
       └─> Updates mods.json with version info

2. TRANSLATION PHASE (External - Weblate)
   └─> Translators edit pl.json on Weblate
   └─> Weblate commits changes to repository
   └─> Files: mods/<mod-name>/assets/*/lang/pl.json

3. BUILD PHASE
   └─> scripts/mods.cs build <version>
       ├─> Compiles TranslationReloader.dll (C#)
       ├─> Merges all complete pl.json files
       ├─> Creates modinfo.json
       ├─> Packages into .zip with loader DLL
       └─> Generates changelog and history

4. RUNTIME PHASE (In-Game)
   └─> TranslationReloader.dll loads
       ├─> ExecuteOrder() = double.MaxValue (loads LAST)
       ├─> Uses reflection to move pack Origin to end of list
       └─> Reloads translations (Polish files override originals)
```

---

## FILE STRUCTURE

```
/home/k1llo/VintageStory-Weblate-Sync/
│
├── README.md                           # Main documentation
├── VintageStory-Weblate-Sync.sln      # Visual Studio solution file
├── mods.json                          # Database of tracked mods (modid, version, lastUpdated)
├── translators.txt                    # List of translator names (for credits)
│
├── game/                              # Base game translations
│   ├── en.json                        # English source (14,353 lines)
│   └── pl.json                        # Polish translation (6,694 lines)
│
├── mods/                              # Mod translations directory
│   ├── <Mod Name>/                    # One folder per mod (e.g., "Butchering")
│   │   └── assets/
│   │       └── <modid>/               # Mod's asset namespace
│   │           └── lang/
│   │               ├── en.json        # English source (extracted by update)
│   │               └── pl.json        # Polish translation (edited on Weblate)
│   │
│   └── [77 total mod folders]
│
├── scripts/
│   └── mods.cs                        # Main build script (1034 lines, C# script)
│                                      # Commands: fix, update, build
│
├── TranslationReloader/               # C# mod project
│   ├── TranslationReloader.csproj     # .NET 8.0 project file
│   ├── TranslationReloaderMod.cs      # Main mod class (79 lines)
│   ├── README.md                      # Build instructions
│   └── .gitignore                     # Build artifacts
│
└── dist/                              # Build output directory (created by script)
    ├── PolishTranslationsPack_v<version>.zip
    ├── changelog_<version>.txt
    └── build-history.json
```

---

## KEY COMPONENTS

### 1. mods.json - Mod Database
**Location:** `/home/k1llo/VintageStory-Weblate-Sync/mods.json`  
**Format:** JSON array of mod objects  
**Purpose:** Track which mods to update and their versions

**Schema:**
```json
[
  {
    "name": "Mod Display Name",        // Human-readable name
    "modid": "moddb_identifier",       // ModDB API identifier
    "version": "1.2.3",                // Current downloaded version
    "lastUpdated": "2025-11-20"        // UTC date of last update
  }
]
```

**Usage:**
- `update` command: Determines which mods to check for updates
- `build` command: Provides version info for changelog
- Contains 77+ mods currently tracked

---

### 2. scripts/mods.cs - Build Automation Script
**Location:** `/home/k1llo/VintageStory-Weblate-Sync/scripts/mods.cs`  
**Language:** C# script (dotnet script)  
**Lines:** 1034  
**Dependencies:**
- Newtonsoft.Json@13.0.4 (JSON parsing)
- Semver@3.0.0 (version comparison)

#### Commands

##### A. `fix` - JSON Formatter
```bash
dotnet scripts/mods.cs fix
```
**Purpose:** Normalize JSON files
**Actions:**
- Converts CRLF → LF line endings
- Reformats with 4-space indentation
- Processes all *.json in `mods/` and `game/`
**Use Case:** Clean up after manual edits or Weblate commits

##### B. `update` - Mod Synchronizer
```bash
dotnet scripts/mods.cs update
```
**Purpose:** Download latest English translations from ModDB
**Process:**
1. Fetches recently updated mods from API (last 24-48h)
2. For each mod in mods.json:
   - Checks ModDB API for latest version
   - Compares with current version (semver)
   - Downloads mod zip if newer
   - Extracts all `*/lang/en.json` files
   - Saves to `mods/<name>/assets/*/lang/en.json`
   - Updates mods.json with new version/date
3. Creates `update-log.txt` if changes made

**Output Files:**
- `mods.json` (updated versions)
- `update-log.txt` (summary of changes)
- English source files in mod folders

**Important:** Does NOT touch pl.json files (translator responsibility)

##### C. `build <version> [--no-history]` - Package Builder
```bash
# Test build
dotnet scripts/mods.cs build test-20260101 --no-history

# Release build
dotnet scripts/mods.cs build 1.0.0
```

**Purpose:** Create distributable mod package
**Parameters:**
- `<version>`: Version string (e.g., "1.0.0", "test-20260101")
- `--no-history`: Skip saving to build-history.json

**Build Process:**
1. **Validation Phase:**
   - For each mod folder in `mods/`:
     - Find all en.json and pl.json files
     - Merge multiple files per mod (if exist)
     - Count translated vs total strings
     - Compute SHA256 hash of pl.json
     - Mark as complete (100%) or incomplete

2. **Compilation Phase:**
   - Runs `dotnet build` on TranslationReloader project
   - Produces `TranslationReloader.dll`

3. **Assembly Phase:**
   - Creates temp build directory
   - Generates `modinfo.json` with metadata
   - Merges all COMPLETE pl.json files (incomplete excluded)
   - Preserves asset path structure

4. **Packaging Phase:**
   - Creates ZIP archive
   - Includes all merged pl.json files
   - Includes TranslationReloader.dll (root of zip)
   - Includes modicon.png (if exists)
   - Includes changelog.txt

5. **Changelog Generation:**
   - Compares with previous build (from build-history.json)
   - Detects: Added mods, Updated mods (version change), Fixed translations (hash change)
   - Creates two versions:
     - `changelog.txt` (inside zip): Changes only
     - `changelog_<version>.txt` (in dist/): Changes + incomplete list

6. **History Tracking:**
   - Saves build metadata to `build-history.json`
   - Stores: version, date, timestamp, mod count, mod list with hashes
   - Enables changelog diff for next build

**Output Files:**
- `dist/PolishTranslationsPack_v<version>.zip` - Main deliverable
- `dist/changelog_<version>.txt` - Detailed changelog
- `dist/build-history.json` - Build history database (unless --no-history)

**Quality Control:**
- Only includes mods with 100% complete translations
- Warns about incomplete translations in output
- Logs translation coverage for all mods

---

### 3. TranslationReloader - Runtime Loader Mod
**Location:** `/home/k1llo/VintageStory-Weblate-Sync/TranslationReloader/`  
**Language:** C# (.NET 8.0)  
**Purpose:** Ensure Polish translations load AFTER all mods

#### Technical Implementation

**File:** TranslationReloaderMod.cs (79 lines)

**Class:** `TranslationReloaderMod : ModSystem`

**Key Method 1: ExecuteOrder()**
```csharp
public override double ExecuteOrder() => double.MaxValue;
```
**Effect:** Forces this mod to initialize LAST (highest execution order)

**Key Method 2: AssetsLoaded(ICoreAPI api)**
**Execution:** After all mod assets loaded
**Algorithm:**
1. Find Polish Translations Pack's Origin in asset system
   - Searches for origin with path containing "polishtranslationspack"
2. Use reflection to access private `Origins` field
   - `api.Assets.GetType().GetField("Origins", ...)`
3. Move pack's Origin to END of list
   - Remove from current position
   - Append to end
4. Invalidate current translation cache
5. Reload all translations with `Lang.Load()`

**Why This Works:**
- Vintage Story loads assets in Origin order
- Later Origins override earlier ones
- By moving to end, Polish translations override all mod translations
- Reflection needed because Origins list is internal API

**Dependencies:**
- `VintagestoryAPI.dll` (from $VINTAGE_STORY environment variable)
- Requires .NET 8.0 SDK to build

**Build Command:**
```bash
cd TranslationReloader
dotnet build -c Release
```

**Output:** `TranslationReloader/bin/Release/TranslationReloader.dll`

---

### 4. translators.txt - Credits File
**Location:** `/home/k1llo/VintageStory-Weblate-Sync/translators.txt`  
**Format:** Plain text, one name per line  
**Current Contributors:**
- Zsuatem
- ManChrzan
- Nessie_XII

**Usage:**
- `build` command reads this file
- Names added to `modinfo.json` authors array
- If missing/empty: uses "Community Translators" as default

---

### 5. Game Translation Files
**Location:** `/home/k1llo/VintageStory-Weblate-Sync/game/`

**en.json:**
- 14,353 lines
- Base game English strings
- Source for Polish translation

**pl.json:**
- 6,694 lines
- Base game Polish translation
- Coverage: ~47% (partial translation)

**Note:** These are for reference/tracking but NOT included in mod build  
(Base game translations handled separately by game devs)

---

## DATA FLOW

### Translation Key Structure
```
{
  "item-deadbear-*": "Niedźwiedź (martwy)",
  "itemdesc-deadbear-*": "Ciężar zwierzęcia mocno ci ciąży",
  ...
}
```

**Key Format:** `<category>-<identifier>[-<variant>]`  
**Wildcards:** `*` matches any variant

### Asset Path Preservation
**Original mod structure:**
```
ModName.zip/
└── assets/
    └── modid/
        └── lang/
            └── en.json
```

**Translation pack structure:**
```
PolishTranslationsPack.zip/
├── modinfo.json
├── TranslationReloader.dll
└── assets/
    └── modid/
        └── lang/
            └── pl.json
```

**Critical:** Asset paths must match exactly for overrides to work

---

## BUILD SYSTEM DETAILS

### Version Comparison
**Library:** Semver@3.0.0  
**Method:** `CompareVersions(string v1, string v2)`  
**Handles:**
- Semantic versioning (1.2.3)
- Pre-release tags (1.0.0-rc.1)
- Development versions (2.0.0-dev.11)
- Fallback to string comparison if parse fails

### JSON Normalization
**Class:** `NormalizingJsonTextReader`  
**Purpose:** Handle CRLF in JSON strings during parsing  
**Action:** Converts `\r\n` → `\n` and `\r` → `\n`

### Hash Computation
**Algorithm:** SHA256  
**Purpose:** Detect translation changes between builds  
**Process:**
1. Recursively sort JSON object keys
2. Serialize to compact JSON (no whitespace)
3. Hash UTF-8 bytes
4. Return lowercase hex string

**Use Case:** Distinguishes "translation fixes" from "version updates" in changelog

---

## EXTERNAL INTEGRATIONS

### ModDB API
**Base URL:** `https://mods.vintagestory.at/api/`

**Endpoints Used:**
1. **`/api/mods`** - List all mods
   - Returns: Array of mods with last release dates
   - Used by: `update` command to filter recently updated mods

2. **`/api/mod/{modid}`** - Get mod details
   - Returns: Mod metadata + releases array
   - Used by: `update` command to get latest version and download URL

**Response Structure:**
```json
{
  "mod": {
    "releases": [
      {
        "modversion": "1.2.3",
        "mainfile": "https://mods.vintagestory.at/download?fileid=..."
      }
    ]
  }
}
```

### Weblate Platform
**Integration Type:** Git-based (direct repository commits)  
**Workflow:**
1. Weblate detects `en.json` files as source strings
2. Translators edit `pl.json` files via web interface
3. Weblate commits changes directly to this repository
4. No special API integration needed - standard Git sync

**Files Managed by Weblate:**
- All `mods/*/assets/*/lang/pl.json` files
- NOT managed by script (script only handles en.json)

---

## ENVIRONMENT REQUIREMENTS

### Build System
**Required:**
- .NET 10.0 SDK (for dotnet script execution)
- .NET 8.0 SDK (for TranslationReloader compilation)

**Environment Variable:**
```bash
export VINTAGE_STORY="/path/to/game"
# Windows: $env:VINTAGE_STORY = "C:\Program Files\Vintagestory"
```
**Purpose:** Locate VintagestoryAPI.dll for mod compilation

### Runtime (In-Game)
**Required:**
- Vintage Story game (client-side)
- Mod type: "code" (contains DLL)
- Side: "client" (only needed on player's client)

---

## ERROR HANDLING

### Update Command Resilience
- **API Failure:** Logs warning, continues with other mods
- **Download Failure:** Logs error, skips mod
- **Invalid JSON:** Saves raw file, logs warning
- **Missing en.json:** Logs error, skips mod
- **No recent updates:** Skips mod (optimization)

### Build Command Validation
- **Missing en.json:** Warning, skips mod
- **Missing pl.json:** Warning, skips mod
- **Incomplete translation:** Warning, excluded from build
- **TranslationReloader build fail:** Warning, continues without DLL
- **Reflection failure (in-game):** Logs error, translations may not override

---

## DEVELOPMENT WORKFLOW

### Typical Release Cycle
```
1. NEW MODS ADDED
   └─> Update mods.json manually with new modid
   
2. WEEKLY/MONTHLY SYNC
   └─> dotnet scripts/mods.cs update
   └─> Creates update-log.txt with changes
   └─> Commit to Git
   
3. WEBLATE TRANSLATION
   └─> Translators work on Weblate platform
   └─> Weblate auto-commits pl.json changes
   
4. PRE-RELEASE BUILD
   └─> dotnet scripts/mods.cs build test-YYYYMMDD --no-history
   └─> Test in-game
   
5. RELEASE BUILD
   └─> dotnet scripts/mods.cs build X.Y.Z
   └─> Upload PolishTranslationsPack_vX.Y.Z.zip to ModDB
   └─> Post changelog
```

### Testing Checklist
1. Build completes without errors
2. ZIP contains TranslationReloader.dll
3. ZIP contains modinfo.json with correct version
4. In-game: Polish translations visible
5. In-game: Mod loads last (check ExecuteOrder logs)
6. In-game: Translations override base mod versions

---

## KNOWN LIMITATIONS

### Translation Coverage
- Only includes mods with 100% complete translations
- Incomplete mods excluded from build (intentional quality control)
- Base game translations separate (not included in mod)

### Technical Constraints
- Requires reflection to access internal API (brittle)
- Breaking API changes in future game versions may break loader
- DLL must be in mod root (not in subdirectory)

### Build System
- No incremental builds (always full rebuild)
- No parallel downloads (mods fetched sequentially)
- Manual addition of new mods required (no auto-discovery)

---

## MAINTENANCE NOTES

### Adding New Mod
1. Get modid from ModDB URL
2. Add entry to mods.json:
   ```json
   {
     "name": "Display Name",
     "modid": "moddb_identifier",
     "version": ""
   }
   ```
3. Run `dotnet scripts/mods.cs update`
4. Verify en.json created in mods/ folder
5. Wait for Weblate to sync (or create pl.json manually)

### Updating Script Dependencies
**File:** `scripts/mods.cs` header
```csharp
#:package Newtonsoft.Json@13.0.4
#:package Semver@3.0.0
```
Change versions as needed for updates

### Debugging Build Issues
**Enable verbose logging:**
- Script uses colored console output
- Red = Error
- Yellow = Warning
- Green = Success
- Cyan = Info

**Common Issues:**
1. "Cannot access Origins field" → Game API changed, update reflection code
2. "No en.json files" → Mod structure changed, verify asset paths
3. "Failed to parse JSON" → Invalid JSON from ModDB, manual cleanup needed

---

## SECURITY CONSIDERATIONS

### Download Safety
- Downloads from official ModDB only
- No checksum verification (trust ModDB)
- Temporary files cleaned up after extraction

### Reflection Usage
- Accesses private API fields (by design)
- Read-only operations after modification
- No persistence beyond game session

### Build Artifacts
- No sensitive data in outputs
- Changelog shows mod versions (public info)
- Build history local only (not in mod package)

---

## PERFORMANCE CHARACTERISTICS

### Update Command
- API calls: O(n) where n = number of mods
- Downloads: Only updated mods (filtered by date)
- Typical time: 1-5 minutes for 77 mods

### Build Command
- Compilation: ~5-10 seconds
- File I/O: O(m) where m = number of translation files
- Hashing: O(k) where k = total translation keys
- Typical time: 30-60 seconds

### Runtime Loader
- Initialization: <100ms
- Reflection overhead: Minimal (one-time)
- No runtime performance impact

---

## FILE FORMAT SPECIFICATIONS

### modinfo.json (Generated)
```json
{
  "type": "code",
  "side": "client",
  "name": "Polish Translations Pack",
  "modid": "polishtranslationspack",
  "description": "Polish Translations Pack - a collection of...",
  "website": "https://mods.vintagestory.at/polishtranslationspack",
  "version": "1.0.0",
  "authors": ["Zsuatem", "ManChrzan", "Nessie_XII"],
  "dependencies": {
    "game": ""
  }
}
```

### build-history.json Structure
```json
[
  {
    "version": "1.0.0",
    "date": "2026-01-01",
    "timestamp": "2026-01-01T12:00:00.0000000Z",
    "modsCount": 50,
    "mods": [
      {
        "name": "Butchering",
        "version": "1.10.15",
        "hash": "abc123..."
      }
    ]
  }
]
```
**Ordering:** Newest first (index 0)

---

## GLOSSARY

**Terms:**
- **Origin:** Vintage Story's asset source system (mod, game, pack)
- **ModDB:** Official Vintage Story mod distribution platform
- **Weblate:** Open-source translation management platform
- **ExecuteOrder:** Mod initialization order (higher = later)
- **Semver:** Semantic Versioning (major.minor.patch)
- **DLL:** Dynamic Link Library (.NET assembly)

**File Extensions:**
- `.cs` - C# source code
- `.csproj` - C# project file (MSBuild)
- `.sln` - Visual Studio solution file
- `.json` - JSON data/translation file

---

## CRITICAL SUCCESS FACTORS

For this system to work correctly:

1. **Asset Path Matching:** Translation paths must exactly match original mod paths
2. **Load Order:** TranslationReloader must load last (ExecuteOrder = MaxValue)
3. **Origin Manipulation:** Reflection must successfully move Origin to end of list
4. **Complete Translations:** Only 100% complete mods included (quality over quantity)
5. **Weblate Sync:** Git commits from Weblate must preserve file structure
6. **Version Tracking:** mods.json must stay in sync with ModDB releases

---

## FUTURE ENHANCEMENT IDEAS

**Potential Improvements:**
1. Automated new mod discovery via ModDB API
2. Partial translation inclusion (with opt-in flag)
3. Multi-language support (extend beyond Polish)
4. Automated testing in game environment
5. Incremental builds (hash-based change detection)
6. Parallel mod downloads
7. Build artifacts signing/verification
8. Translation progress dashboard

---

## END OF ANALYSIS

This document contains complete technical understanding of the codebase as of 2026-01-01.
All major files, workflows, and systems documented above.

**For AI Assistant:**
- Use this as reference for code modifications
- Update this document when significant changes made
- Refer to specific sections when answering user questions
- Cross-reference with actual code when in doubt
