"""
Script to investigate پزشکی faculty requests and find associated employee names.
Date range: 1404-08-01 to 1404-09-01
"""

import sqlite3
from pathlib import Path
from collections import defaultdict

# Database path
DB_PATH = Path(__file__).parent / 'database' / 'hami.db'

# پزشکی faculty keywords (from analyzer.py FACULTY mapping)
PEZESHKI_KEYWORDS = ["پزشکی", "پرستاری", "اتاق عمل", "هوشبری"]

# Date range
START_DATE = "1404-08-01"
END_DATE = "1404-09-01"

def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def main():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Build query for پزشکی faculty requests in date range
    field_conditions = " OR ".join([f"field LIKE '%{kw}%'" for kw in PEZESHKI_KEYWORDS])
    
    # Get all requests in پزشکی faculty within date range
    query = f"""
        SELECT id, reference_code, name as student_name, field, first_date
        FROM requests
        WHERE ({field_conditions})
        AND first_date >= ?
        AND first_date < ?
        ORDER BY first_date
    """
    
    cursor.execute(query, (START_DATE, END_DATE))
    requests = cursor.fetchall()
    
    print(f"=" * 80)
    print(f"پزشکی Faculty Investigation")
    print(f"Date Range: {START_DATE} to {END_DATE}")
    print(f"Keywords used: {PEZESHKI_KEYWORDS}")
    print(f"=" * 80)
    print(f"\nTotal requests found: {len(requests)}")
    
    # Track employee receivers for each request
    employee_to_requests = defaultdict(list)  # employee_name -> list of (reference_code, student_name, field)
    request_to_employees = {}  # reference_code -> list of employee names
    
    for req in requests:
        request_id = req['id']
        reference_code = req['reference_code']
        student_name = req['student_name']
        field = req['field']
        
        # Get all messages for this request where receiver is an employee
        # Employee = NOT student email pattern AND NOT a place (ending with 4 digits)
        cursor.execute("""
            SELECT DISTINCT to_name
            FROM messages
            WHERE request_id = ?
            AND to_name NOT IN ('<empty>', 'Not in workflow')
            AND NOT (to_email GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]@iau.ir')
            AND NOT (to_name GLOB '*[0-9][0-9][0-9][0-9]')
        """, (request_id,))
        
        employees = [row['to_name'] for row in cursor.fetchall()]
        request_to_employees[reference_code] = employees
        
        for emp in employees:
            employee_to_requests[emp].append({
                'reference_code': reference_code,
                'student_name': student_name,
                'field': field
            })
    
    # Print summary of unique employees
    print(f"\n{'=' * 80}")
    print(f"UNIQUE EMPLOYEE RECEIVERS (sorted by request count)")
    print(f"{'=' * 80}")
    
    sorted_employees = sorted(employee_to_requests.items(), key=lambda x: len(x[1]), reverse=True)
    
    print(f"\n{'Employee Name':<40} | {'Request Count':<15}")
    print("-" * 60)
    
    for emp_name, reqs in sorted_employees:
        print(f"{emp_name:<40} | {len(reqs):<15}")
    
    print(f"\n{'=' * 80}")
    print(f"TOTAL UNIQUE EMPLOYEES: {len(employee_to_requests)}")
    print(f"{'=' * 80}")
    
    # Print detailed breakdown per employee
    print(f"\n{'=' * 80}")
    print(f"DETAILED BREAKDOWN: Employee -> Requests")
    print(f"{'=' * 80}")
    
    for emp_name, reqs in sorted_employees:
        print(f"\n>>> {emp_name} ({len(reqs)} requests)")
        for req in reqs[:10]:  # Show first 10
            print(f"    - {req['reference_code']} | {req['student_name']} | {req['field'][:50]}...")
        if len(reqs) > 10:
            print(f"    ... and {len(reqs) - 10} more")
    
    # Export to CSV for easier analysis
    csv_output = Path(__file__).parent / 'pezeshki_investigation.csv'
    with open(csv_output, 'w', encoding='utf-8-sig') as f:
        f.write("employee_name,request_count,reference_codes\n")
        for emp_name, reqs in sorted_employees:
            ref_codes = "|".join([r['reference_code'] for r in reqs])
            f.write(f'"{emp_name}",{len(reqs)},"{ref_codes}"\n')
    
    print(f"\n{'=' * 80}")
    print(f"Exported to: {csv_output}")
    print(f"{'=' * 80}")
    
    # Also show requests with NO employee receivers
    no_employee_requests = [ref for ref, emps in request_to_employees.items() if not emps]
    if no_employee_requests:
        print(f"\n{'=' * 80}")
        print(f"REQUESTS WITH NO EMPLOYEE RECEIVERS: {len(no_employee_requests)}")
        print(f"{'=' * 80}")
        for ref in no_employee_requests[:20]:
            print(f"  - {ref}")
        if len(no_employee_requests) > 20:
            print(f"  ... and {len(no_employee_requests) - 20} more")
    
    conn.close()

if __name__ == "__main__":
    main()
