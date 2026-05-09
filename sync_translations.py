#!/usr/bin/env python3
"""
Translation synchronization script for Vintage Story mod translations.
Compares en.json and be.json files, reports missing keys, and rebuilds translations.
"""

SCRIPT_VERSION = "3.5-SUPPORT-COMMENTS"

import json
import re
import sys
import os
from pathlib import Path
from collections import OrderedDict
from typing import Dict, List, Tuple, Any


def parse_json_with_order(filepath: str) -> Tuple[OrderedDict, List[str]]:
    """Parse JSON file preserving key order and original lines."""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()
        original_lines = content.split('\n')
    
    # Remove comments (lines starting with //)
    lines_without_comments = []
    for line in original_lines:
        # Check if line is a comment
        stripped = line.strip()
        if stripped.startswith('//'):
            # Keep as blank line to preserve line numbers
            lines_without_comments.append('')
        else:
            lines_without_comments.append(line)
    
    content_without_comments = '\n'.join(lines_without_comments)
    
    # Remove trailing commas for valid JSON parsing
    fixed_content = re.sub(r',(\s*[}\]])', r'\1', content_without_comments)
    data = json.loads(fixed_content, object_pairs_hook=OrderedDict)
    
    return data, original_lines


def get_all_keys_with_paths(obj, prefix='') -> Dict[str, Any]:
    """Get all keys with their full paths and values."""
    result = OrderedDict()
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                nested = get_all_keys_with_paths(value, full_key)
                result.update(nested)
            else:
                result[full_key] = value
    
    return result


def format_value(value) -> str:
    """Format a value for JSON output."""
    if isinstance(value, str):
        # Use json.dumps for proper escaping
        return json.dumps(value, ensure_ascii=False)
    elif isinstance(value, bool):
        return 'true' if value else 'false'
    elif value is None:
        return 'null'
    else:
        return json.dumps(value, ensure_ascii=False)


def get_modid(en_file: str) -> str:
    """Extract modid from modinfo.json or folder name."""
    mod_folder = Path(en_file).parent.parent.parent.parent
    modinfo_path = mod_folder / 'modinfo.json'
    
    if modinfo_path.exists():
        with open(modinfo_path, 'r', encoding='utf-8') as f:
            modinfo = json.load(f)
            modid = modinfo.get('modid', modinfo.get('modId'))
            if modid:
                return modid
    
    # Fallback to folder name
    return mod_folder.name.lower().replace(' ', '')


def rebuild_translation_file(en_file: str, be_file: str) -> None:
    """Rebuild be.json using en.json structure, preserving translations and blank lines."""
    
    # Parse files
    en_data, _ = parse_json_with_order(en_file)
    be_translations = {}
    if os.path.exists(be_file):
        be_data, _ = parse_json_with_order(be_file)
        be_translations = get_all_keys_with_paths(be_data)
    
    en_keys = get_all_keys_with_paths(en_data)
    
    # Build translation lookup
    added_keys = {}
    stats = {'added': 0, 'kept': 0, 'removed': len(be_translations) - len(set(be_translations.keys()) & set(en_keys.keys()))}
    
    for key in en_keys:
        if key not in be_translations:
            added_keys[key] = en_keys[key]
            stats['added'] += 1
        else:
            stats['kept'] += 1
    
    # Read en.json line by line to preserve blank lines and formatting
    with open(en_file, 'r', encoding='utf-8-sig') as f:
        en_lines = f.readlines()
    
    # Process each line
    new_lines = []
    pattern = r'"([^"]+)"\s*:\s*(.+?)(?:,\s*)?$'
    
    for line in en_lines:
        # Check if line is blank or structural (braces)
        if line.strip() in ['', '{', '}', '},']:
            new_lines.append(line)
            continue
        
        # Check if line contains a key-value pair
        match = re.search(pattern, line)
        if match:
            key = match.group(1)
            # Use BE translation if available, otherwise keep EN value
            if key in be_translations:
                # Replace the value with BE translation
                be_value = be_translations[key]
                be_json = json.dumps(be_value, ensure_ascii=False)
                # Preserve the line's indentation and comma
                indent = len(line) - len(line.lstrip())
                has_comma = line.rstrip().endswith(',')
                new_line = ' ' * indent + f'"{key}": {be_json}'
                if has_comma:
                    new_line += ','
                new_line += '\n'
                new_lines.append(new_line)
            else:
                # Keep EN line as-is
                new_lines.append(line)
        else:
            # Keep line as-is if we can't parse it
            new_lines.append(line)
    
    # Write the new file preserving blank lines
    with open(be_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    # Create temp file with untranslated keys
    if added_keys:
        todo_dir = Path('translations_todo')
        todo_dir.mkdir(exist_ok=True)
        
        modid = get_modid(en_file)
        temp_file = todo_dir / f"{modid}_be.json"
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(added_keys, f, ensure_ascii=False, indent=2)
        
        print(f"\\n📝 Created temp file: {temp_file}")
        print(f"   Contains {len(added_keys)} keys to translate")
        # Also write a small metadata file so we know the intended target when merging
        meta_file = temp_file.with_suffix('.meta.json')
        try:
            with open(meta_file, 'w', encoding='utf-8') as mf:
                json.dump({'be_file': str(be_file), 'en_file': str(en_file)}, mf, ensure_ascii=False, indent=2)
            print(f"   Wrote metadata: {meta_file}")
        except Exception:
            pass
    
    # Print summary
    print(f"\\n✅ Rebuilt {be_file}")
    print(f"\\n📊 Statistics:")
    print(f"  Total keys in EN: {len(en_keys)}")
    print(f"  Kept translations: {stats['kept']}")
    print(f"  Added from EN (need translation): {stats['added']}")
    print(f"  Removed obsolete keys: {stats['removed']}")
    
    if stats['removed'] > 0:
        removed_keys = set(be_translations.keys()) - set(en_keys.keys())
        print(f"\\n🗑️  Removed obsolete keys: {min(10, len(removed_keys))} shown")
        for key in list(removed_keys)[:10]:
            print(f"  - {key}")
        if len(removed_keys) > 10:
            print(f"  ... and {len(removed_keys) - 10} more")


def merge_translations(temp_file: str, be_file: str) -> None:
    """Merge translations from temp file into be.json, preserving blank lines."""
    
    if not os.path.exists(temp_file) or not os.path.exists(be_file):
        print(f"❌ Error: File not found")
        return
    
    # Load translations from temp file
    with open(temp_file, 'r', encoding='utf-8') as f:
        new_translations = json.load(f)
    
    # Read be.json line by line to preserve formatting
    with open(be_file, 'r', encoding='utf-8-sig') as f:
        be_lines = f.readlines()
    
    # Build new content preserving blank lines
    new_lines = []
    merged_count = 0
    pattern = r'"([^"]+)"\s*:\s*(.+?)(\s*)$'
    
    for line in be_lines:
        # Check if this is a key-value line
        match = re.search(pattern, line)
        if match:
            key = match.group(1)
            old_value_with_comma = match.group(2).strip()
            trailing_spaces = match.group(3)
            
            # Check if original had a comma
            has_comma = old_value_with_comma.endswith(',')
            old_value = old_value_with_comma.rstrip(',').strip()
            
            # If this key has a new translation, replace it
            if key in new_translations:
                new_value = json.dumps(new_translations[key], ensure_ascii=False)
                # Get proper indentation from original line
                indent = line[:line.index('"')]
                # Add comma if original had one
                comma = ',' if has_comma else ''
                # Don't add extra \n - trailing_spaces already has it or line doesn't end with one
                if trailing_spaces or line.endswith('\n'):
                    new_line = f'{indent}"{key}": {new_value}{comma}\n'
                else:
                    new_line = f'{indent}"{key}": {new_value}{comma}'
                new_lines.append(new_line)
                merged_count += 1
            else:
                # Keep original line as-is (already has newline)
                new_lines.append(line)
        else:
            # Not a key-value line (blank line, brackets, etc.) - keep as-is
            new_lines.append(line)
    
    # Write back to be.json
    with open(be_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"\\n✅ Merged {merged_count} translations into {be_file}")
    
    # Delete temp file
    try:
        os.remove(temp_file)
        print(f"🗑️  Deleted temp file: {temp_file}")
    except Exception as e:
        print(f"⚠️  Could not delete temp file: {e}")
    # Also delete metadata file if present
    try:
        meta_path = Path(temp_file).with_suffix('.meta.json')
        if meta_path.exists():
            os.remove(meta_path)
            print(f"🗑️  Deleted metadata file: {meta_path}")
    except Exception as e:
        print(f"⚠️  Could not delete metadata file: {e}")


def compare_translations(en_file: str, be_file: str) -> None:
    """Compare en.json and be.json and generate a report."""
    
    en_data, _ = parse_json_with_order(en_file)
    be_data, _ = parse_json_with_order(be_file)
    
    en_keys = get_all_keys_with_paths(en_data)
    be_keys = get_all_keys_with_paths(be_data)
    
    missing_in_be = set(en_keys.keys()) - set(be_keys.keys())
    extra_in_be = set(be_keys.keys()) - set(en_keys.keys())
    common_keys = set(en_keys.keys()) & set(be_keys.keys())
    
    completion = (len(common_keys) / len(en_keys) * 100) if en_keys else 100
    
    # Generate report
    print(f"\\n{'='*70}")
    print(f"Translation Comparison Report")
    print(f"{'='*70}")
    print(f"English file: {en_file}")
    print(f"Belarusian file: {be_file}")
    print(f"\\n📊 Statistics:")
    print(f"  Total keys in EN: {len(en_keys)}")
    print(f"  Total keys in BE: {len(be_keys)}")
    print(f"  Common keys: {len(common_keys)}")
    print(f"  Missing in BE: {len(missing_in_be)}")
    print(f"  Extra in BE: {len(extra_in_be)}")
    print(f"  Completion: {completion:.1f}%")
    
    if missing_in_be:
        print(f"\\n⚠️  Missing keys in BE ({len(missing_in_be)}):")
        for key in list(sorted(missing_in_be))[:10]:
            value = en_keys[key]
            display_value = value if len(str(value)) < 60 else str(value)[:57] + "..."
            print(f"  - {key}")
            print(f"    EN: {display_value}")
        if len(missing_in_be) > 10:
            print(f"  ... and {len(missing_in_be) - 10} more")
    
    if extra_in_be:
        print(f"\\n❓ Extra keys in BE (not in EN) ({len(extra_in_be)}):")
        for key in list(sorted(extra_in_be))[:10]:
            print(f"  + {key}")
        if len(extra_in_be) > 10:
            print(f"  ... and {len(extra_in_be) - 10} more")
    
    print(f"\\n{'='*70}\\n")


def find_translation_files(mod_path: str) -> List[Tuple[str, str]]:
    """Find all en.json and be.json file pairs in a mod directory."""
    mod_path_obj = Path(mod_path)
    
    # Search for lang files
    en_files = list(mod_path_obj.rglob('**/lang/en.json'))
    
    if not en_files:
        raise FileNotFoundError(f"No en.json found in {mod_path}")
    
    # For each en.json, find corresponding be.json
    pairs = []
    missing_be = []
    
    for en_file in en_files:
        be_file = en_file.parent / 'be.json'
        if be_file.exists():
            pairs.append((str(en_file), str(be_file)))
        else:
            missing_be.append(str(en_file))
    
    if missing_be:
        print(f"\\n⚠️  Found EN files without corresponding BE files:")
        for f in missing_be:
            print(f"  - {f}")
            # Create the be.json path
            be_path = Path(f).parent / 'be.json'
            pairs.append((f, str(be_path)))
            print(f"    Will create: {be_path}")
    
    if len(pairs) > 1:
        print(f"\\n📂 Found {len(pairs)} translation file pairs in this mod")
    
    return pairs


def main():
    print("=" * 70)
    print("Vintage Story Translation Synchronization Tool")
    print(f"Version: {SCRIPT_VERSION}")
    print("=" * 70)
    
    # Get mod path or file paths
    file_pairs = []
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if os.path.isdir(arg):
            try:
                file_pairs = find_translation_files(arg)
            except FileNotFoundError as e:
                print(f"❌ Error: {e}")
                sys.exit(1)
        else:
            # Assume it's a path pattern
            if 'en.json' in arg:
                en_file = arg
                be_file = arg.replace('en.json', 'be.json')
                file_pairs = [(en_file, be_file)]
            else:
                print("❌ Error: Please provide a directory or en.json file path")
                sys.exit(1)
    else:
        # Interactive mode
        mod_path = input("\\nEnter mod directory path (or press Enter for current directory): ").strip()
        if not mod_path:
            mod_path = "."
        
        try:
            file_pairs = find_translation_files(mod_path)
        except FileNotFoundError as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    # Main loop
    while True:
        # Show menu
        print("\\n" + "=" * 70)
        print("Choose an option:")
        print("  1) Compare files and show report")
        print("  2) Rebuild BE from EN (creates temp file for translation)")
        print("  3) Merge translations from temp file back to BE")
        print("  0) Exit")
        print("=" * 70)
        
        choice = input("\\nYour choice: ").strip()
        
        if choice == '1':
            for en_file, be_file in file_pairs:
                print(f"\\n📂 Processing pair:")
                print(f"  EN: {en_file}")
                print(f"  BE: {be_file}")
                
                if not os.path.exists(en_file):
                    print(f"❌ Error: {en_file} not found")
                    continue
                
                if os.path.exists(be_file):
                    compare_translations(en_file, be_file)
                else:
                    print(f"⚠️  {be_file} does not exist yet")
                    # Show en.json info
                    en_data, _ = parse_json_with_order(en_file)
                    en_keys = get_all_keys_with_paths(en_data)
                    print(f"  EN file has {len(en_keys)} keys that need translation")
                
        elif choice == '2':
            total_processed = 0
            for en_file, be_file in file_pairs:
                print(f"\\n📂 Processing pair:")
                print(f"  EN: {en_file}")
                print(f"  BE: {be_file}")
                
                if not os.path.exists(en_file):
                    print(f"❌ Error: {en_file} not found")
                    continue
                
                # If be.json doesn't exist, offer to create it
                if not os.path.exists(be_file):
                    print(f"\\n⚠️  {be_file} does not exist")
                    create = input("Create new be.json from en.json template? (y/N): ").strip().lower()
                    if create != 'y':
                        print("⏭️  Skipping this file")
                        continue
                else:
                    # Show preview
                    be_data, _ = parse_json_with_order(be_file)
                    en_data, _ = parse_json_with_order(en_file)
                    be_keys = get_all_keys_with_paths(be_data)
                    en_keys = get_all_keys_with_paths(en_data)
                    
                    missing = len(set(en_keys.keys()) - set(be_keys.keys()))
                    obsolete = len(set(be_keys.keys()) - set(en_keys.keys()))
                    
                    print(f"\\n📊 Preview:")
                    print(f"  Missing keys: {missing}")
                    print(f"  Obsolete keys: {obsolete}")
                    print(f"  ⚠️  This will REBUILD {be_file} using EN structure")
                    
                    confirm = input(f"Rebuild {be_file}? (y/N): ").strip().lower()
                    if confirm != 'y':
                        print("⏭️  Skipped")
                        continue
                
                rebuild_translation_file(en_file, be_file)
                total_processed += 1
            
            if total_processed > 0:
                print(f"\\n✅ Processed {total_processed} file(s)")
                print(f"\\n💡 Next: Translate files in translations_todo/ folder")
                print(f"   Then run option 3 to merge translations back")
                
        elif choice == '3':
            # Find and merge temp files
            todo_dir = Path('translations_todo')
            if not todo_dir.exists() or not list(todo_dir.glob('*.json')):
                print("\\n⚠️  No temp files found in translations_todo/")
                print("   Run option 2 first to create temp files")
            else:
                temp_files = list(todo_dir.glob('*_be.json'))
                print(f"\n📂 Found {len(temp_files)} temp file(s):")
                for i, tf in enumerate(temp_files, 1):
                    print(f"  {i}. {tf.name}")

                # Process each temp file. Use metadata if present to locate the exact target.
                for temp_file in temp_files:
                    meta_file = temp_file.with_suffix('.meta.json')
                    target_be = None
                    en_file_from_meta = None

                    if meta_file.exists():
                        try:
                            with open(meta_file, 'r', encoding='utf-8') as mf:
                                meta = json.load(mf)
                                target_be = meta.get('be_file')
                                en_file_from_meta = meta.get('en_file')
                        except Exception:
                            target_be = None

                    # Fallback: try to match by modid among discovered file_pairs
                    if not target_be:
                        temp_modid = temp_file.stem.replace('_be', '')
                        for en_file, be_file in file_pairs:
                            if get_modid(en_file) == temp_modid:
                                target_be = be_file
                                break

                    if not target_be:
                        print(f"\n⚠️  Could not find target for {temp_file.name}; please merge manually")
                        continue

                    print(f"\n📂 Processing: {temp_file.stem}")
                    print(f"  Temp file: {temp_file}")
                    print(f"  Target: {target_be}")

                    confirm = input(f"Merge translations? (y/N): ").strip().lower()
                    if confirm == 'y':
                        merge_translations(str(temp_file), target_be)
                    else:
                        print("⏭️  Skipped")
                
        elif choice == '0':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    main()
