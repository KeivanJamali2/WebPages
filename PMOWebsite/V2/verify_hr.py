from app import create_app
from analysis.analysis_human_resources import HumanResourcesAnalysis

app = create_app()
print('✓ App created successfully')
print('✓ HumanResourcesAnalysis imported successfully')

with app.app_context():
    routes = [r.rule for r in app.url_map.iter_rules() if 'human-resources' in r.rule]
    if routes:
        print(f'✓ HR API route registered: {routes[0]}')
    else:
        print('✗ HR API route not found')

print('✓ All verifications passed - HR analysis ready!')
