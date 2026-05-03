#!/usr/bin/env python3
"""
Translation Report Generator for Vintage Story mods.
Analyzes translation completion across all mods and generates an HTML report.
Does NOT modify any source files.
"""

import json
import re
import sys
import os
from pathlib import Path
from collections import OrderedDict
from typing import Dict, List, Tuple, Any
from datetime import datetime


def parse_json_with_order(filepath: str) -> Tuple[OrderedDict, List[str]]:
    """Parse JSON file preserving key order and original lines."""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()
        original_lines = content.split('\n')
    
    # Remove comments (lines starting with //)
    lines_without_comments = []
    for line in original_lines:
        stripped = line.strip()
        if stripped.startswith('//'):
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


def get_modid(en_file: str) -> str:
    """Extract modid from modinfo.json or folder name."""
    mod_folder = Path(en_file).parent.parent.parent.parent
    modinfo_path = mod_folder / 'modinfo.json'
    
    if modinfo_path.exists():
        try:
            with open(modinfo_path, 'r', encoding='utf-8') as f:
                modinfo = json.load(f)
                modid = modinfo.get('modid', modinfo.get('modId'))
                if modid:
                    return modid
        except Exception:
            pass
    
    # Fallback to folder name
    return mod_folder.name.replace(' ', '_')


def find_translation_files(mod_path: str) -> List[Tuple[str, str]]:
    """Find all en.json and be.json file pairs in a directory."""
    mod_path_obj = Path(mod_path)
    en_files = list(mod_path_obj.rglob('**/lang/en.json'))
    
    pairs = []
    for en_file in en_files:
        be_file = en_file.parent / 'be.json'
        pairs.append((str(en_file), str(be_file)))
        
    return pairs


def generate_html_report(stats_list: List[Dict], output_file: str = "translation_report.html"):
    """Generate a responsive HTML report from the statistics."""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vintage Story Mod Translation Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }}
        .summary-cards {{
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            justify-content: center;
        }}
        .card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            flex: 1;
            max-width: 200px;
        }}
        .card h3 {{
            margin: 0;
            font-size: 14px;
            color: #7f8c8d;
            text-transform: uppercase;
        }}
        .card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #2980b9;
            margin: 10px 0 0 0;
        }}
        .table-container {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 15px 20px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
            position: sticky;
            top: 0;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .progress-bar-container {{
            width: 100%;
            background-color: #eee;
            border-radius: 4px;
            height: 20px;
            position: relative;
            overflow: hidden;
        }}
        .progress-bar {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }}
        .progress-text {{
            position: absolute;
            width: 100%;
            text-align: center;
            top: 0;
            line-height: 20px;
            font-size: 12px;
            font-weight: bold;
            color: #333;
            text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
        }}
        .timestamp {{
            text-align: center;
            color: #7f8c8d;
            margin-top: 30px;
            font-size: 14px;
        }}
        .missing-count {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .completed {{
            color: #27ae60;
        }}
    </style>
</head>
<body>
    <h1>🌍 Mod Translation Status</h1>
"""

    total_en = sum(s['en_keys'] for s in stats_list)
    total_be = sum(s['be_keys'] for s in stats_list)
    total_missing = sum(s['missing'] for s in stats_list)
    overall_completion = ((total_en - total_missing) / total_en * 100) if total_en > 0 else 100

    html += f"""
    <div class="summary-cards">
        <div class="card">
            <h3>Total Mods</h3>
            <p class="value">{len(stats_list)}</p>
        </div>
        <div class="card">
            <h3>Total Strings (EN)</h3>
            <p class="value">{total_en}</p>
        </div>
        <div class="card">
            <h3>Missing Translations</h3>
            <p class="value missing-count">{total_missing}</p>
        </div>
        <div class="card">
            <h3>Overall Completion</h3>
            <p class="value">{overall_completion:.1f}%</p>
        </div>
    </div>

    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Mod ID</th>
                    <th>EN Keys</th>
                    <th>BE Keys</th>
                    <th>Missing</th>
                    <th>Extra</th>
                    <th>Completion</th>
                </tr>
            </thead>
            <tbody>
"""

    # Sort primarily by completion (lowest first), then by mod ID
    sorted_stats = sorted(stats_list, key=lambda x: (x['completion'], x['modid']))

    for stat in sorted_stats:
        comp = stat['completion']
        color = "#27ae60" if comp == 100 else "#f1c40f" if comp > 80 else "#e67e22" if comp > 50 else "#e74c3c"
        
        missing_display = f'<span class="missing-count">{stat["missing"]}</span>' if stat['missing'] > 0 else '-'
        extra_display = stat['extra'] if stat['extra'] > 0 else '-'
        
        html += f"""
                <tr>
                    <td><strong>{stat['modid']}</strong><br><small style="color:#7f8c8d">{stat['en_file']}</small></td>
                    <td>{stat['en_keys']}</td>
                    <td>{stat['be_keys']}</td>
                    <td>{missing_display}</td>
                    <td>{extra_display}</td>
                    <td>
                        <div class="progress-bar-container">
                            <div class="progress-bar" style="width: {comp}%; background-color: {color};"></div>
                            <div class="progress-text">{comp:.1f}%</div>
                        </div>
                    </td>
                </tr>
"""

    html += f"""
            </tbody>
        </table>
    </div>

    <p class="timestamp">Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ HTML report generated successfully: {output_file}")


def main():
    print("=" * 60)
    print("Translation Report Generator")
    print("=" * 60)

    mod_path = "."
    if len(sys.argv) > 1:
        mod_path = sys.argv[1]
        
    print(f"Scanning directory: {os.path.abspath(mod_path)} ...")
    
    try:
        file_pairs = find_translation_files(mod_path)
    except Exception as e:
        print(f"❌ Error finding files: {e}")
        sys.exit(1)

    if not file_pairs:
        print("❌ No en.json files found.")
        sys.exit(1)
        
    print(f"Found {len(file_pairs)} English translation files. Analyzing...\n")

    stats = []

    for en_file, be_file in file_pairs:
        try:
            en_data, _ = parse_json_with_order(en_file)
            en_keys = get_all_keys_with_paths(en_data)
        except Exception as e:
            print(f"⚠️ Could not parse EN file {en_file}: {e}")
            continue

        modid = get_modid(en_file)
        
        en_count = len(en_keys)
        be_count = 0
        missing = en_count
        extra = 0
        
        if os.path.exists(be_file):
            try:
                be_data, _ = parse_json_with_order(be_file)
                be_keys = get_all_keys_with_paths(be_data)
                be_count = len(be_keys)
                
                missing = len(set(en_keys.keys()) - set(be_keys.keys()))
                extra = len(set(be_keys.keys()) - set(en_keys.keys()))
            except Exception as e:
                print(f"⚠️ Could not parse BE file {be_file}: {e}")
                
        completion = ((en_count - missing) / en_count * 100) if en_count > 0 else 100
        
        # Make path relative for cleaner display
        try:
            rel_en_file = os.path.relpath(en_file, mod_path)
        except ValueError:
            rel_en_file = en_file
            
        stats.append({
            'modid': modid,
            'en_file': rel_en_file,
            'en_keys': en_count,
            'be_keys': be_count,
            'missing': missing,
            'extra': extra,
            'completion': completion
        })

    if stats:
        generate_html_report(stats)
    else:
        print("❌ No data to report.")

if __name__ == "__main__":
    main()
