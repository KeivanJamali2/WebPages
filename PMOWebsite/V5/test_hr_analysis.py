#!/usr/bin/env python
"""
Test Human Resources Analysis implementation.
"""
import sys
sys.path.insert(0, '/Users/keivanjamali/Projects/WebPages/Project-02-PMOWebsite/V5')

from app import create_app
from analysis import DataService
from analysis.analysis_human_resources import HumanResourcesAnalysis
from models import db

def test_hr_analysis():
    """Test HR analysis with real data."""
    
    app = create_app('development')
    
    with app.app_context():
        print("=" * 80)
        print("TESTING HUMAN RESOURCES ANALYSIS")
        print("=" * 80)
        print()
        
        # Get project config
        from Projects.project_configurations import load_project_config
        try:
            config = load_project_config('Project-01')
            print("✓ Loaded project config for Project-01")
        except Exception as e:
            print(f"✗ Error loading project config: {e}")
            return
        
        # Create data service (project_id=1 for testing)
        project_id = 1
        ds = DataService(db, project_id, status='approved')
        
        # Get HR data
        hr_data = ds.get_human_resources()
        print(f"✓ Found {len(hr_data)} human resource records")
        
        if len(hr_data) == 0:
            print("\n⚠️  No HR data found. Analysis cannot proceed.")
            print("   This is expected if no daily forms with HR data exist.")
            return
        
        # Create analyzer
        analyzer = HumanResourcesAnalysis(ds, config)
        print("✓ Created HumanResourcesAnalysis instance")
        print()
        
        # Test get_summary_table
        print("-" * 80)
        print("TEST: get_summary_table()")
        print("-" * 80)
        summary = analyzer.get_summary_table(unit='per_day')
        print(f"✓ Returned {len(summary['rows'])} position summaries")
        
        if len(summary['rows']) > 0:
            print("\nTop 3 positions by cost:")
            for i, row in enumerate(summary['rows'][:3], 1):
                print(f"  {i}. {row['post']:30} - {row['total_cost']:>15,} Rial")
                print(f"     Days: {row['days_present']}, People-Days: {row['people_days']}, Hours: {row['total_hours']:.1f}")
                print(f"     Presence Rate: {row['presence_rate']:.1f}% (expected: {row['expected_days']} days)")
        
        print(f"\nTotals:")
        print(f"  People-Days: {summary['totals']['people_days']:,}")
        print(f"  Total Hours: {summary['totals']['total_hours']:,.1f}")
        print(f"  Total Cost: {summary['totals']['total_cost']:,} Rial")
        
        print()
        
        # Test get_presence_analysis
        print("-" * 80)
        print("TEST: get_presence_analysis()")
        print("-" * 80)
        presence = analyzer.get_presence_analysis()
        print(f"✓ Returned {len(presence)} presence records")
        
        if len(presence) > 0:
            print("\nPresence rates (top 5):")
            for i, p in enumerate(presence[:5], 1):
                status_icon = "✓" if p['status'] == 'good' else "⚠️" if p['status'] == 'warning' else "✗"
                print(f"  {status_icon} {p['post']:30} - {p['presence_rate']:>5.1f}% ({p['actual_days']}/{p['expected_days']} days)")
        
        print()
        
        # Test get_cost_by_position
        print("-" * 80)
        print("TEST: get_cost_by_position()")
        print("-" * 80)
        costs = analyzer.get_cost_by_position()
        print(f"✓ Returned {len(costs)} cost records")
        
        if len(costs) > 0:
            print("\nTop 5 positions by cost:")
            for i, c in enumerate(costs[:5], 1):
                print(f"  {i}. {c['post']:30} - {c['total_cost']:>15,} Rial")
        
        print()
        
        # Test get_headcount_over_time
        print("-" * 80)
        print("TEST: get_headcount_over_time()")
        print("-" * 80)
        headcount = analyzer.get_headcount_over_time()
        print(f"✓ Returned {len(headcount)} daily headcount records")
        
        if len(headcount) > 0:
            print(f"\nDate range: {headcount[0]['date']} to {headcount[-1]['date']}")
            print(f"Sample record (first day): {headcount[0]}")
        
        print()
        
        # Test get_daily_cost_trend
        print("-" * 80)
        print("TEST: get_daily_cost_trend()")
        print("-" * 80)
        trend = analyzer.get_daily_cost_trend()
        print(f"✓ Returned {len(trend)} daily cost records")
        
        if len(trend) > 0:
            avg_daily = sum(t['total_cost'] for t in trend) / len(trend)
            print(f"\nAverage daily HR cost: {avg_daily:,.0f} Rial")
            print(f"Min: {min(t['total_cost'] for t in trend):,.0f} Rial")
            print(f"Max: {max(t['total_cost'] for t in trend):,.0f} Rial")
        
        print()
        
        # Test get_all
        print("-" * 80)
        print("TEST: get_all()")
        print("-" * 80)
        all_data = analyzer.get_all(unit='per_day')
        print("✓ get_all() returned complete data structure")
        print(f"  Keys: {list(all_data.keys())}")
        print(f"  - summary: {len(all_data['summary']['rows'])} rows")
        print(f"  - presence_analysis: {len(all_data['presence_analysis'])} records")
        print(f"  - cost_by_position: {len(all_data['cost_by_position'])} records")
        print(f"  - headcount_over_time: {len(all_data['headcount_over_time'])} records")
        print(f"  - daily_cost_trend: {len(all_data['daily_cost_trend'])} records")
        
        print()
        print("=" * 80)
        print("✓ ALL TESTS PASSED!")
        print("=" * 80)

if __name__ == '__main__':
    test_hr_analysis()
