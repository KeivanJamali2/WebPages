"""
PMO Website - Run Script

Simple script to run the application.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == '__main__':
    print("=" * 70)
    print(" PMO Website - Development Server".center(70))
    print("=" * 70)
    print()
    print("  Server URL: http://127.0.0.1:5000")
    print("  Environment: Development")
    print()
    print("  Default Admin Login:")
    print("    Email: admin@company.com")
    print("    Password: admin123")
    print()
    print("  Press CTRL+C to quit")
    print("=" * 70)
    print()
    
    # Run the application
    app.run(
        host='0.0.0.0',  # Accessible from network
        port=5000,
        debug=True,
        use_reloader=True
    )
