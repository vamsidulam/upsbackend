#!/usr/bin/env python3
"""
Update MongoDB Connection Strings Script
This script updates all Python files to use MongoDB Atlas instead of localhost
"""

import os
import re
import glob
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# MongoDB Atlas connection string
ATLAS_MONGODB_URI = os.getenv("MONGODB_URI")

# Patterns to search and replace
REPLACEMENTS = [
    # Direct localhost connections
    (r'mongodb+srv://vamsidulam11:vamsi2005121@cluster0.4kq3vjn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0', ATLAS_MONGODB_URI),
    (r'mongodb+srv://vamsidulam11:vamsi2005121@cluster0.4kq3vjn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0/', ATLAS_MONGODB_URI),
    
    # Environment variable defaults
    (r'os\.getenv\("MONGODB_URI", "mongodb+srv://vamsidulam11:vamsi2005121@cluster0.4kq3vjn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"\)', 
     f'os.getenv("MONGODB_URI", "{ATLAS_MONGODB_URI}")'),
    
    # Hardcoded localhost in variables
    (r'= "mongodb+srv://vamsidulam11:vamsi2005121@cluster0.4kq3vjn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"', f'= "{ATLAS_MONGODB_URI}"'),
    (r'= "mongodb+srv://vamsidulam11:vamsi2005121@cluster0.4kq3vjn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0/"', f'= "{ATLAS_MONGODB_URI}"'),
    
    # MongoClient instantiations
    (r'MongoClient\("mongodb+srv://vamsidulam11:vamsi2005121@cluster0.4kq3vjn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"\)', f'MongoClient("{ATLAS_MONGODB_URI}")'),
    (r'MongoClient\("mongodb+srv://vamsidulam11:vamsi2005121@cluster0.4kq3vjn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0/"\)', f'MongoClient("{ATLAS_MONGODB_URI}")'),
]

def update_file(file_path):
    """Update a single file with new connection strings"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all replacements
        for old_pattern, new_pattern in REPLACEMENTS:
            content = re.sub(old_pattern, new_pattern, content)
        
        # Check if any changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated: {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def find_python_files(directory):
    """Find all Python files in the directory"""
    python_files = []
    
    # Search for .py files
    for pattern in ['**/*.py', '*.py']:
        python_files.extend(glob.glob(os.path.join(directory, pattern), recursive=True))
    
    # Remove duplicates and sort
    python_files = sorted(list(set(python_files)))
    
    return python_files

def main():
    """Main function to update all Python files"""
    print("🔧 MongoDB Connection String Update Script")
    print("=" * 60)
    print(f"🔄 Updating connection strings to MongoDB Atlas")
    print(f"📍 Atlas URI: {ATLAS_MONGODB_URI[:50]}...")
    print()
    
    # Get current directory
    current_dir = os.getcwd()
    print(f"📁 Working directory: {current_dir}")
    
    # Find all Python files
    python_files = find_python_files(current_dir)
    
    if not python_files:
        print("❌ No Python files found")
        return
    
    print(f"📋 Found {len(python_files)} Python files")
    print()
    
    # Update each file
    updated_count = 0
    for file_path in python_files:
        if update_file(file_path):
            updated_count += 1
    
    print()
    print("📊 Update Summary:")
    print(f"   Total files processed: {len(python_files)}")
    print(f"   Files updated: {updated_count}")
    print(f"   Files unchanged: {len(python_files) - updated_count}")
    
    if updated_count > 0:
        print()
        print("🎉 Connection strings updated successfully!")
        print("📝 Next steps:")
        print("   1. Test your application with the new Atlas connection")
        print("   2. Run the migration script to move your data")
        print("   3. Verify all functionality works with Atlas")
    else:
        print()
        print("ℹ️  No files needed updates")

if __name__ == "__main__":
    main()
