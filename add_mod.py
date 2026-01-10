#!/usr/bin/env python3
"""
Script to add a new mod from zip archive to the translation project.
Extracts en.json files and updates mods.json database.
"""

import argparse
import json
import os
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path


def find_file_in_zip(zip_ref, filename):
    """Find a file in the zip archive (case-insensitive)."""
    for item in zip_ref.namelist():
        if item.lower().endswith(filename.lower()):
            return item
    return None


def extract_modinfo(zip_path):
    """Extract and parse modinfo.json from the zip archive."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            modinfo_path = find_file_in_zip(zip_ref, 'modinfo.json')
            
            if not modinfo_path:
                raise Exception(f"❌ Error: modinfo.json not found in {zip_path}")
            
            with zip_ref.open(modinfo_path) as f:
                modinfo = json.load(f)
            
            # Normalize modID to modid (some mods use different case)
            if 'modID' in modinfo and 'modid' not in modinfo:
                modinfo['modid'] = modinfo['modID']
            
            # Normalize Version to version (some mods use different case)
            if 'Version' in modinfo and 'version' not in modinfo:
                modinfo['version'] = modinfo['Version']
            
            # Validate required fields
            required_fields = ['name', 'modid', 'version']
            missing_fields = [field for field in required_fields if field not in modinfo]
            
            if missing_fields:
                raise Exception(f"❌ Error: modinfo.json missing required fields: {', '.join(missing_fields)}")
            
            return modinfo
    except zipfile.BadZipFile:
        raise Exception(f"❌ Error: {zip_path} is not a valid zip archive")
    except json.JSONDecodeError:
        raise Exception(f"❌ Error: modinfo.json contains invalid JSON")


def find_en_json_files(zip_path):
    """Find all en.json files under assets/*/lang/ in the zip."""
    en_json_files = []
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for item in zip_ref.namelist():
            # Look for pattern: assets/*/lang/en.json (with or without leading slash)
            item_lower = item.lower()
            if item_lower.endswith('/lang/en.json') or item_lower.endswith('\\lang\\en.json'):
                if 'assets/' in item_lower or 'assets\\' in item_lower:
                    en_json_files.append(item)
    
    return en_json_files


def extract_assets_path(full_path):
    """Extract the assets/* portion of the path."""
    # Find 'assets/' in the path and return everything from there
    lower_path = full_path.lower()
    assets_index = lower_path.find('/assets/')
    
    if assets_index == -1:
        assets_index = lower_path.find('assets/')
        if assets_index == -1:
            return full_path
        return full_path[assets_index:]
    
    return full_path[assets_index + 1:]  # Skip the leading /


def create_mod_structure(zip_path, mod_name, mods_dir):
    """Create the mod folder structure and extract en.json files."""
    mod_folder = mods_dir / mod_name
    en_json_files = find_en_json_files(zip_path)
    
    if not en_json_files:
        print(f"⚠️  Warning: No en.json files found in {zip_path}")
        return 0
    
    print(f"📁 Creating folder: {mod_folder}")
    mod_folder.mkdir(parents=True, exist_ok=True)
    
    extracted_count = 0
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for en_json_path in en_json_files:
            # Extract relative path from assets/ onwards
            relative_path = extract_assets_path(en_json_path)
            target_path = mod_folder / relative_path
            
            # Create parent directories
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Extract the file
            with zip_ref.open(en_json_path) as source:
                with open(target_path, 'wb') as target:
                    shutil.copyfileobj(source, target)
            
            print(f"   ✓ Extracted: {relative_path}")
            extracted_count += 1
    
    return extracted_count


def update_mods_json(modinfo, mods_json_path):
    """Update mods.json with the new mod entry."""
    # Read existing mods.json
    if mods_json_path.exists():
        with open(mods_json_path, 'r', encoding='utf-8') as f:
            mods_data = json.load(f)
    else:
        mods_data = []
    
    # Check if mod already exists
    existing_mod = None
    existing_index = -1
    for idx, mod in enumerate(mods_data):
        if mod.get('modid') == modinfo['modid']:
            existing_mod = mod
            existing_index = idx
            break
    
    if existing_mod:
        print(f"\n⚠️  Mod '{modinfo['name']}' (modid: {modinfo['modid']}) already exists in mods.json:")
        print(f"   Current version: {existing_mod.get('version', 'N/A')}")
        print(f"   New version: {modinfo['version']}")
        
        while True:
            response = input("   Update? (y/n): ").lower().strip()
            if response == 'y':
                mods_data[existing_index] = {
                    "name": modinfo['name'],
                    "modid": modinfo['modid'],
                    "version": modinfo['version'],
                    "lastUpdated": datetime.now().strftime("%Y-%m-%d")
                }
                print("   ✓ Updated existing entry")
                break
            elif response == 'n':
                print("   ✗ Skipped updating mods.json")
                return False
    else:
        # Add new entry
        new_entry = {
            "name": modinfo['name'],
            "modid": modinfo['modid'],
            "version": modinfo['version'],
            "lastUpdated": datetime.now().strftime("%Y-%m-%d")
        }
        mods_data.append(new_entry)
        print(f"✓ Added new entry to mods.json")
    
    # Write back to mods.json with formatting
    with open(mods_json_path, 'w', encoding='utf-8') as f:
        json.dump(mods_data, f, indent=4, ensure_ascii=False)
        f.write('\n')  # Add trailing newline
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Add a new mod from zip archive to the translation project'
    )
    parser.add_argument(
        '-f', '--file',
        required=True,
        help='Path to the mod zip archive'
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    zip_path = Path(args.file).resolve()
    script_dir = Path(__file__).parent
    mods_dir = script_dir / 'mods'
    mods_json_path = script_dir / 'mods.json'
    
    # Validate zip file exists
    if not zip_path.exists():
        print(f"❌ Error: File not found: {zip_path}")
        sys.exit(1)
    
    try:
        print(f"📦 Processing: {zip_path.name}")
        print()
        
        # Step 1: Extract modinfo
        print("🔍 Reading modinfo.json...")
        modinfo = extract_modinfo(zip_path)
        print(f"   Name: {modinfo['name']}")
        print(f"   ModID: {modinfo['modid']}")
        print(f"   Version: {modinfo['version']}")
        print()
        
        # Step 2: Create mod structure
        print("📂 Extracting en.json files...")
        extracted_count = create_mod_structure(zip_path, modinfo['name'], mods_dir)
        print(f"   Total files extracted: {extracted_count}")
        print()
        
        # Step 3: Update mods.json
        print("📝 Updating mods.json...")
        updated = update_mods_json(modinfo, mods_json_path)
        print()
        
        # Summary
        print("✅ Done!")
        print(f"\nNext steps:")
        print(f"1. Add Belarusian translations to: mods/{modinfo['name']}/assets/*/lang/be.json")
        print(f"2. Run: dotnet scripts/mods.cs -r linux-x64 -- build <version>")
        
    except Exception as e:
        print(f"\n{str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
