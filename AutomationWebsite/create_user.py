#!/usr/bin/env python3
"""
User Management Utility
Helper script for admins to create and manage users with plain text passwords.

Usage:
    python create_user.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.auth.auth_manager import AuthManager


def create_user_interactive():
    """Interactive user creation."""
    print("=" * 60)
    print("User Creation Utility")
    print("=" * 60)
    
    # Get user details
    email = input("\nEnter user email: ").strip()
    if not email or '@' not in email:
        print("❌ Invalid email address")
        return
    
    name = input("Enter user full name: ").strip()
    if not name:
        print("❌ Name cannot be empty")
        return
    
    password = input("Enter initial password (min 4 characters): ").strip()
    if len(password) < 4:
        print("❌ Password must be at least 4 characters long")
        return
    
    print("\nAvailable tools:")
    print("  - connect: Connect to admin files")
    print("  - share: Share files")
    print("  - generic: Generic cross-section processing")
    print("  - ppk: PPK GPS data processing")
    print("  - csdp: CSDP profile processing")
    print("  - image: Image processing")
    print("  - delete_distance: Distance filtering")
    print("  - culvert: Culvert processing")
    print("  - assistant: AI chat assistant")
    
    tools_input = input("\nEnter allowed tools (comma-separated): ").strip()
    allowed_tools = [tool.strip() for tool in tools_input.split(',') if tool.strip()]
    
    if not allowed_tools:
        print("❌ At least one tool must be specified")
        return
    
    # Create user
    print("\n" + "-" * 60)
    print(f"Creating user: {email}")
    print(f"Name: {name}")
    print(f"Allowed tools: {', '.join(allowed_tools)}")
    print("-" * 60)
    
    confirm = input("\nConfirm creation? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("❌ User creation cancelled")
        return
    
    # Initialize auth manager
    users_csv = os.path.join(os.path.dirname(__file__), 'data', 'users.csv')
    auth_manager = AuthManager(users_csv)
    
    # Create user
    success, message = auth_manager.create_user(email, name, password, allowed_tools)
    
    if success:
        print(f"\n✅ {message}")
        print(f"\nUser can now login with:")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print("\n⚠️  User should change password after first login")
    else:
        print(f"\n❌ {message}")


def show_users():
    """Display all existing users."""
    print("=" * 60)
    print("Current Users")
    print("=" * 60)
    
    users_csv = os.path.join(os.path.dirname(__file__), 'data', 'users.csv')
    
    if not os.path.exists(users_csv):
        print("\n❌ No users file found")
        return
    
    import pandas as pd
    try:
        users = pd.read_csv(users_csv)
        if users.empty:
            print("\n📝 No users registered yet")
            return
        
        print(f"\n{'Email':<30} {'Name':<25} {'Password':<15} {'Tools'}")
        print("-" * 100)
        
        for _, user in users.iterrows():
            email = user['email']
            name = user['name']
            password = user['password']
            tools = user['allowed_tools'].replace(',', ', ')
            print(f"{email:<30} {name:<25} {password:<15} {tools}")
        
        print(f"\nTotal users: {len(users)}")
    
    except Exception as e:
        print(f"\n❌ Error reading users: {e}")


def main():
    """Main menu."""
    while True:
        print("\n" + "=" * 60)
        print("User Management Utility")
        print("=" * 60)
        print("\n1. Create new user")
        print("2. Show all users")
        print("3. Exit")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == '1':
            create_user_interactive()
        elif choice == '2':
            show_users()
        elif choice == '3':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid option")


if __name__ == '__main__':
    main()
