# Proposed Project Structure

This document outlines a proposed new structure for the project to improve organization and maintainability.

## Key Changes
- **`src` directory**: Houses all core application source code.
- **`data` directory**: Centralizes all JSON data files.
- **`docs` directory**: Contains all markdown and documentation files.
- **`scripts` directory**: For all utility, diagnostic, and runner scripts.
- **`tests` directory**: Contains all tests.
- **File Renaming**: Some core files are renamed for clarity.
- **Root Directory**: Cleaned up to only contain project-level files.

## Proposed Structure
```
.
├── data/
│   ├── class_levels.json
│   ├── real_timetable.json
│   ├── teacher_full_names.json
│   ├── teacher_levels.json
│   ├── teacher_name_map.json
│   └── teacher_subjects.json
├── docs/
│   ├── CLAUDE.md
│   ├── GEMINI.md
│   ├── LINE_BOT_SETUP.md
│   ├── NEXT_STEPS.md
│   ├── project_structure.md
│   ├── SESSION_SUMMARY.md
│   ├── TEST_REPORT.md
│   └── TESTING.md
├── scripts/
│   ├── add_absence_to_sheets.py
│   ├── check_conflicts.py
│   ├── check_prathom_periods.py
│   ├── check_t011_duplicates.py
│   ├── create_sheets_template.py
│   ├── diagnose_excel.py
│   ├── fix_sheet_headers.py
│   └── run_all_tests.py
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── timetable/
│   │   ├── __init__.py
│   │   ├── ai_parser.py
│   │   ├── converter.py         # Renamed from excel_converting.py
│   │   └── substitute.py        # Renamed from find_substitute.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── build_teacher_data.py
│   │   ├── daily_leave_processor.py # Renamed from process_daily_leaves.py
│   │   └── leave_log_sync.py      # Renamed from sync_leave_logs.py
│   └── web/
│       ├── __init__.py
│       ├── line_messaging.py
│       └── webhook.py
├── tests/
│   ├── __init__.py
│   ├── test_converter.py        # Renamed from test_excel_converting.py
│   ├── test_period_parsing.py
│   ├── test_real_timetable.py
│   └── test_substitute.py       # Rename from test_find_substitute.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```