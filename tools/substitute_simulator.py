"""
Interactive Substitute Teacher Simulator

This tool allows manual testing of substitute assignment scenarios with detailed explanations.

Usage:
    # Interactive mode
    python tools/substitute_simulator.py

    # Command-line mode
    python tools/substitute_simulator.py --teacher T004 --day Mon --periods 1,2,3

    # Load from scenario file
    python tools/substitute_simulator.py --scenario scenarios/monday_busy.json

    # Verbose output
    python tools/substitute_simulator.py -t T004 -d Mon -p 1-6 --verbose
"""

import sys
import os
import json
import argparse
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.timetable.substitute import find_best_substitute_teacher, assign_substitutes_for_day
from src.config import config


def load_data():
    """Load all necessary data files"""
    with open(config.TIMETABLE_FILE, 'r', encoding='utf-8') as f:
        timetable = json.load(f)

    with open(config.TEACHER_SUBJECTS_FILE, 'r', encoding='utf-8') as f:
        teacher_subjects = json.load(f)

    with open(config.TEACHER_LEVELS_FILE, 'r', encoding='utf-8') as f:
        teacher_levels = json.load(f)

    with open(config.CLASS_LEVELS_FILE, 'r', encoding='utf-8') as f:
        class_levels = json.load(f)

    with open(config.TEACHER_FULL_NAMES_FILE, 'r', encoding='utf-8') as f:
        teacher_names = json.load(f)

    all_teacher_ids = list(teacher_subjects.keys())

    return {
        'timetable': timetable,
        'teacher_subjects': teacher_subjects,
        'teacher_levels': teacher_levels,
        'class_levels': class_levels,
        'teacher_names': teacher_names,
        'all_teacher_ids': all_teacher_ids
    }


def parse_periods(periods_str: str) -> List[int]:
    """Parse period string like '1,2,3' or '1-6' into list of integers"""
    periods = []
    parts = periods_str.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            # Range like '1-6'
            start, end = part.split('-')
            periods.extend(range(int(start), int(end) + 1))
        else:
            # Single period
            periods.append(int(part))
    return sorted(set(periods))  # Remove duplicates and sort


def format_teacher_info(teacher_id: str, teacher_subjects: Dict, teacher_levels: Dict, teacher_names: Dict) -> str:
    """Format teacher information for display"""
    name = teacher_names.get(teacher_id, teacher_id)
    subjects = teacher_subjects.get(teacher_id, [])
    levels = teacher_levels.get(teacher_id, [])

    return f"{name} ({teacher_id}) - Subjects: {', '.join(subjects[:5])}{'...' if len(subjects) > 5 else ''} - Levels: {', '.join(levels)}"


def run_scenario(absent_teacher: str, day: str, periods: List[int], data: Dict,
                verbose: bool = False, format_type: str = 'text') -> Dict:
    """
    Run a substitute finding scenario

    Returns:
        Dict with scenario details and results
    """
    timetable = data['timetable']
    teacher_subjects = data['teacher_subjects']
    teacher_levels = data['teacher_levels']
    class_levels = data['class_levels']
    all_teacher_ids = data['all_teacher_ids']

    # Find periods where absent teacher is scheduled
    teacher_schedule = [
        entry for entry in timetable
        if entry['teacher_id'] == absent_teacher and entry['day_id'] == day
    ]

    results = []
    substitute_logs = []  # Track assignments to prevent double-booking

    for period in periods:
        # Find what the teacher is supposed to teach this period
        scheduled = next(
            (e for e in teacher_schedule if e['period_id'] == period),
            None
        )

        if not scheduled:
            results.append({
                'period': period,
                'status': 'not_scheduled',
                'message': f"Absent teacher not scheduled for period {period}"
            })
            continue

        # Find substitute
        substitute = find_best_substitute_teacher(
            subject_id=scheduled['subject_id'],
            day_id=day,
            period_id=period,
            class_id=scheduled['class_id'],
            timetables=timetable,
            teacher_subjects=teacher_subjects,
            substitute_logs=substitute_logs,
            all_teacher_ids=all_teacher_ids,
            absent_teacher_ids=[absent_teacher],
            leave_logs=[],
            teacher_levels=teacher_levels,
            class_levels=class_levels
        )

        # Calculate details
        result = {
            'period': period,
            'class': scheduled['class_id'],
            'subject': scheduled['subject_id'],
            'substitute': substitute,
            'status': 'found' if substitute else 'not_found'
        }

        if substitute:
            # Add to substitute logs for double-booking prevention
            substitute_logs.append({
                'substitute_teacher_id': substitute,
                'day_id': day,
                'period_id': period,
                'class_id': scheduled['class_id'],
                'subject_id': scheduled['subject_id']
            })

            # Check qualifications
            result['can_teach_subject'] = scheduled['subject_id'] in teacher_subjects.get(substitute, [])
            result['level_match'] = class_levels[scheduled['class_id']] in teacher_levels.get(substitute, [])

            # Calculate score (simplified - for display purposes)
            score = 0
            if result['can_teach_subject']:
                score += 2
            if result['level_match']:
                score += 5
            result['score'] = score

            result['reasoning'] = generate_reasoning(result)

        results.append(result)

    return {
        'scenario': {
            'absent_teacher': absent_teacher,
            'day': day,
            'periods': periods
        },
        'results': results,
        'summary': {
            'total_periods': len(results),
            'substitutes_found': sum(1 for r in results if r['status'] == 'found'),
            'not_scheduled': sum(1 for r in results if r['status'] == 'not_scheduled'),
            'success_rate': sum(1 for r in results if r['status'] == 'found') / len([r for r in results if r['status'] != 'not_scheduled']) if results else 0
        }
    }


def generate_reasoning(result: Dict) -> str:
    """Generate human-readable reasoning for substitute selection"""
    reasons = []

    if result['can_teach_subject']:
        reasons.append("Qualified for subject")
    else:
        reasons.append("Not qualified for subject (assigned anyway)")

    if result['level_match']:
        reasons.append("Level match")
    else:
        reasons.append("Level mismatch")

    score = result.get('score', 0)
    if score >= 7:
        reasons.append("Perfect match")
    elif score >= 5:
        reasons.append("Good match")
    elif score >= 2:
        reasons.append("Acceptable match")
    else:
        reasons.append("Last resort")

    return ", ".join(reasons)


def print_text_results(scenario_data: Dict, data: Dict, verbose: bool = False):
    """Print results in text format"""
    scenario = scenario_data['scenario']
    results = scenario_data['results']
    summary = scenario_data['summary']

    teacher_names = data['teacher_names']

    print("\n" + "="*70)
    print("SUBSTITUTE FINDER RESULTS")
    print("="*70)
    print(f"Absent Teacher: {teacher_names.get(scenario['absent_teacher'], scenario['absent_teacher'])}")
    print(f"Day: {scenario['day']}")
    print(f"Periods: {', '.join(map(str, scenario['periods']))}")
    print("="*70)

    for result in results:
        print(f"\nPeriod {result['period']}", end="")

        if result['status'] == 'not_scheduled':
            print(f" - {result['message']}")
            continue

        print(f" - {result['subject']} for {result['class']}")
        print("-" * 70)

        if result['status'] == 'found':
            sub_id = result['substitute']
            sub_name = teacher_names.get(sub_id, sub_id)
            print(f"  Substitute: {sub_name} ({sub_id})")
            print(f"  - Can teach {result['subject']}: {'YES' if result['can_teach_subject'] else 'NO'}")
            print(f"  - Level match: {'YES' if result['level_match'] else 'NO'}")
            print(f"  - Score: {result['score']}")
            print(f"  - Reasoning: {result['reasoning']}")
        else:
            print(f"  NO SUBSTITUTE AVAILABLE")
            print(f"  - All teachers busy or no suitable candidates")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total periods: {summary['total_periods']}")
    print(f"Substitutes found: {summary['substitutes_found']}")
    print(f"Not scheduled: {summary['not_scheduled']}")
    if summary['total_periods'] > summary['not_scheduled']:
        print(f"Success rate: {summary['success_rate']*100:.1f}%")
    print("="*70)


def print_json_results(scenario_data: Dict):
    """Print results in JSON format"""
    print(json.dumps(scenario_data, indent=2, ensure_ascii=False))


def interactive_mode(data: Dict):
    """Run interactive mode"""
    print("\n" + "="*70)
    print("SUBSTITUTE TEACHER SIMULATOR - INTERACTIVE MODE")
    print("="*70)

    while True:
        print("\nSelect mode:")
        print("1. Custom scenario (manual input)")
        print("2. Analyze timetable (view statistics)")
        print("3. Exit")

        choice = input("\nChoice [1-3]: ").strip()

        if choice == '3':
            print("\nGoodbye!")
            break

        elif choice == '1':
            # Custom scenario
            print("\n--- Custom Scenario ---")

            # Get absent teacher
            print(f"\nAvailable teachers: {', '.join(data['all_teacher_ids'])}")
            teacher = input("Which teacher is absent? (e.g., T001): ").strip().upper()

            if teacher not in data['all_teacher_ids']:
                print(f"Error: Invalid teacher ID '{teacher}'")
                continue

            # Get day
            day = input("Which day? [Mon/Tue/Wed/Thu/Fri]: ").strip().capitalize()
            if day not in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
                print(f"Error: Invalid day '{day}'")
                continue

            # Get periods
            periods_str = input("Which periods? (e.g., 1,2,3 or 1-6): ").strip()
            try:
                periods = parse_periods(periods_str)
            except Exception as e:
                print(f"Error parsing periods: {e}")
                continue

            # Run scenario
            print("\nFinding substitutes...")
            scenario_data = run_scenario(teacher, day, periods, data, verbose=False)
            print_text_results(scenario_data, data)

        elif choice == '2':
            # Analyze timetable
            print("\n--- Timetable Statistics ---")
            timetable = data['timetable']

            # Count entries by day
            day_counts = {}
            for entry in timetable:
                day = entry['day_id']
                day_counts[day] = day_counts.get(day, 0) + 1

            print("\nEntries by day:")
            for day, count in sorted(day_counts.items()):
                print(f"  {day}: {count} periods")

            # Count entries by teacher
            teacher_counts = {}
            for entry in timetable:
                teacher = entry['teacher_id']
                teacher_counts[teacher] = teacher_counts.get(teacher, 0) + 1

            print("\nTop 5 busiest teachers:")
            for teacher, count in sorted(teacher_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                name = data['teacher_names'].get(teacher, teacher)
                print(f"  {name}: {count} periods/week")

        else:
            print("Invalid choice. Please select 1, 2, or 3.")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Substitute Teacher Simulator')
    parser.add_argument('-t', '--teacher', help='Absent teacher ID (e.g., T001)')
    parser.add_argument('-d', '--day', help='Day of week (Mon/Tue/Wed/Thu/Fri)')
    parser.add_argument('-p', '--periods', help='Period numbers (e.g., 1,2,3 or 1-6)')
    parser.add_argument('--scenario', help='Load scenario from JSON file')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Output format (text or json)')
    parser.add_argument('--output', help='Save output to file')

    args = parser.parse_args()

    # Load data
    print("Loading data...")
    data = load_data()
    print(f"Loaded {len(data['timetable'])} timetable entries")
    print(f"Found {len(data['all_teacher_ids'])} teachers")

    # Check if running in interactive or CLI mode
    if args.scenario:
        # Load scenario from file
        print(f"\nLoading scenario from {args.scenario}...")
        with open(args.scenario, 'r', encoding='utf-8') as f:
            scenario_config = json.load(f)

        absent_teacher = scenario_config.get('absent_teachers', [])[0]  # Use first teacher
        day = scenario_config['day']
        # Assume all periods for the teacher
        teacher_schedule = [
            e for e in data['timetable']
            if e['teacher_id'] == absent_teacher and e['day_id'] == day
        ]
        periods = sorted(set(e['period_id'] for e in teacher_schedule))

        scenario_data = run_scenario(absent_teacher, day, periods, data, args.verbose, args.format)

        if args.format == 'json':
            print_json_results(scenario_data)
        else:
            print_text_results(scenario_data, data, args.verbose)

    elif args.teacher and args.day and args.periods:
        # CLI mode with parameters
        periods = parse_periods(args.periods)
        scenario_data = run_scenario(args.teacher, args.day, periods, data, args.verbose, args.format)

        if args.format == 'json':
            output = json.dumps(scenario_data, indent=2, ensure_ascii=False)
            print(output)
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output)
                print(f"\nOutput saved to {args.output}")
        else:
            print_text_results(scenario_data, data, args.verbose)

    else:
        # Interactive mode
        interactive_mode(data)


if __name__ == '__main__':
    main()
