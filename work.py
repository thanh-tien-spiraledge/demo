#!/usr/bin/env python3
"""
SQL Validation Script - Based on tend-db-project deploy_scripts.py
Validates SQL files for syntax correctness and structure
"""

import sys
import os
import re
import subprocess
import sqlparse

def get_changed_files():
    """
    Returns a list of files changed in the last commit.
    Based on deploy_scripts.py get_changed_files() function
    """
    try:
        # Get changed files between HEAD~1 and HEAD
        output = subprocess.check_output("git diff --name-only HEAD~1 HEAD", shell=True)
        changed_files = output.decode("utf-8").strip().splitlines()
        return changed_files
    except subprocess.CalledProcessError as err:
        print(f"Error getting changed files: {err}")
        return []

def get_sql_files(changed_files):
    """
    Filter only SQL files from changed files.
    Based on deploy_scripts.py filtering approach
    """
    sql_files = []
    for file in changed_files:
        if file.strip().endswith('.sql'):
            sql_files.append(file.strip())
    return sql_files

def validate_sql_file_content(sql_content, file_path):
    """
    Validate SQL file content based on tend-db-project patterns
    """
    try:
        # Check for basic SQL structure
        if not sql_content.strip():
            return False, "File is empty"
        
        # Parse SQL using sqlparse for syntax validation
        try:
            parsed = sqlparse.parse(sql_content)
            if not parsed:
                return False, "Failed to parse SQL content"
        except Exception as parse_error:
            return False, f"SQL parsing error: {str(parse_error)}"
        
        # Validate based on file type (similar to deploy_scripts.py structure)
        content_upper = sql_content.upper()
        
        # Check for procedure/function files
        if 'CREATE PROCEDURE' in content_upper or 'CREATE FUNCTION' in content_upper:
            return validate_procedure_function(sql_content)
        
        # Check for table files
        elif 'CREATE TABLE' in content_upper or 'ALTER TABLE' in content_upper:
            return validate_table_script(sql_content)
        
        # Check for basic SQL statements
        elif any(keyword in content_upper for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
            return validate_basic_sql(sql_content)
        
        # Check for migration scripts
        elif 'migration' in file_path.lower() or 'script' in file_path.lower():
            return validate_migration_script(sql_content)
        
        else:
            # Generic SQL validation
            return validate_generic_sql(sql_content)
            
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def validate_procedure_function(sql_content):
    """Validate stored procedure or function"""
    content_upper = sql_content.upper()
    
    # Check for proper procedure/function structure
    if 'CREATE PROCEDURE' in content_upper:
        # Check for procedure name
        procedure_match = re.search(r'CREATE PROCEDURE\s+`?([^`\s(]+)`?', sql_content, re.IGNORECASE)
        if not procedure_match:
            return False, "Invalid procedure name or structure"
        
        procedure_name = procedure_match.group(1)
        
        # Check for BEGIN/END blocks
        if 'BEGIN' not in content_upper or 'END' not in content_upper:
            return False, "Procedure missing BEGIN/END block"
        
        return True, f"Valid stored procedure: {procedure_name}"
    
    elif 'CREATE FUNCTION' in content_upper:
        # Check for function name
        function_match = re.search(r'CREATE FUNCTION\s+`?([^`\s(]+)`?', sql_content, re.IGNORECASE)
        if not function_match:
            return False, "Invalid function name or structure"
        
        function_name = function_match.group(1)
        
        # Check for RETURNS clause
        if 'RETURNS' not in content_upper:
            return False, "Function missing RETURNS clause"
        
        return True, f"Valid function: {function_name}"
    
    return False, "Not a valid procedure or function"

def validate_table_script(sql_content):
    """Validate table creation or alteration script"""
    content_upper = sql_content.upper()
    
    if 'CREATE TABLE' in content_upper:
        # Check for table name
        table_match = re.search(r'CREATE TABLE\s+`?([^`\s(]+)`?', sql_content, re.IGNORECASE)
        if not table_match:
            return False, "Invalid table name or structure"
        
        table_name = table_match.group(1)
        
        # Check for column definitions
        if '(' not in sql_content or ')' not in sql_content:
            return False, "Table missing column definitions"
        
        return True, f"Valid table creation: {table_name}"
    
    elif 'ALTER TABLE' in content_upper:
        # Check for table name
        alter_match = re.search(r'ALTER TABLE\s+`?([^`\s]+)`?', sql_content, re.IGNORECASE)
        if not alter_match:
            return False, "Invalid ALTER TABLE structure"
        
        table_name = alter_match.group(1)
        return True, f"Valid table alteration: {table_name}"
    
    return False, "Not a valid table script"

def validate_basic_sql(sql_content):
    """Validate basic SQL statements"""
    content_upper = sql_content.upper()
    
    # Validate SELECT statements
    if 'SELECT' in content_upper:
        if 'FROM' not in content_upper and 'DUAL' not in content_upper:
            return False, "SELECT statement missing FROM clause"
    
    # Validate INSERT statements
    if 'INSERT' in content_upper:
        if 'INTO' not in content_upper:
            return False, "INSERT statement missing INTO clause"
    
    # Validate UPDATE statements
    if 'UPDATE' in content_upper:
        if 'SET' not in content_upper:
            return False, "UPDATE statement missing SET clause"
    
    # Validate DELETE statements
    if 'DELETE' in content_upper:
        if 'FROM' not in content_upper:
            return False, "DELETE statement missing FROM clause"
    
    return True, "Valid SQL statements"

def validate_migration_script(sql_content):
    """Validate migration or script files"""
    # Migration scripts can contain various SQL statements
    content_upper = sql_content.upper()
    
    # Check for common migration patterns
    migration_keywords = ['CREATE', 'ALTER', 'INSERT', 'UPDATE', 'DELETE', 'DROP']
    found_keywords = [kw for kw in migration_keywords if kw in content_upper]
    
    if not found_keywords:
        return False, "Migration script contains no valid SQL operations"
    
    return True, f"Valid migration script with operations: {', '.join(found_keywords)}"

def validate_generic_sql(sql_content):
    """Generic SQL validation"""
    content_upper = sql_content.upper()
    
    # Check for any SQL keywords
    sql_keywords = [
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP',
        'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER',
        'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT'
    ]
    
    found_keywords = [kw for kw in sql_keywords if kw in content_upper]
    
    if not found_keywords:
        return False, "No SQL keywords found"
    
    return True, f"Valid SQL content with keywords: {', '.join(found_keywords)}"

def validate_sql_file(file_path):
    """Validate individual SQL file - main validation function"""
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        
        if not os.path.isfile(file_path):
            return False, f"Not a regular file: {file_path}"
        
        # Check file extension
        if not file_path.lower().endswith('.sql'):
            return False, f"Not a SQL file: {file_path}"
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        if not content.strip():
            return False, "File is empty"
        
        # Get file size for reporting
        file_size = os.path.getsize(file_path)
        line_count = len(content.splitlines())
        
        # Validate SQL content
        is_valid, message = validate_sql_file_content(content, file_path)
        
        if is_valid:
            return True, f"{message} (Size: {file_size} bytes, Lines: {line_count})"
        else:
            return False, f"{message} (Size: {file_size} bytes, Lines: {line_count})"
            
    except Exception as e:
        return False, f"Error processing file {file_path}: {str(e)}"

def main():
    """
    Main validation function - tự động lấy file change và validate
    Based on deploy_scripts.py approach
    """
    print("🔍 SQL Validation Script - tend-db-project style")
    print("=" * 60)
    
    # Get changed files using deploy_scripts.py approach
    print("📋 Getting changed SQL files in this PR...")
    
    try:
        # Get changed files (based on deploy_scripts.py get_changed_files())
        changed_files = get_changed_files()
        
        if not changed_files:
            print("⚠️  No changed files found")
            sys.exit(0)
        
        # Filter only SQL files (based on deploy_scripts.py get_sql_files())
        sql_files = get_sql_files(changed_files)
        
        if not sql_files:
            print("⚠️  No SQL files changed in this PR")
            sys.exit(0)
        
        print(f"📁 Found {len(sql_files)} SQL file(s) to validate:")
        for file in sql_files:
            print(f"   • {file}")
        print()
        
        # Validate each file
        valid_count = 0
        total_count = len(sql_files)
        failed_files = []
        
        for file_path in sql_files:
            print(f"🔍 Validating: {file_path}")
            
            is_valid, message = validate_sql_file(file_path)
            
            if is_valid:
                print(f"   ✅ {message}")
                valid_count += 1
            else:
                print(f"   ❌ {message}")
                failed_files.append(file_path)
            
            print()
        
        # Summary (based on deploy_scripts.py style)
        print("=" * 60)
        print(f"📊 VALIDATION SUMMARY")
        print(f"   Total files: {total_count}")
        print(f"   Passed: {valid_count}")
        print(f"   Failed: {total_count - valid_count}")
        
        if valid_count == total_count:
            print()
            print("🎉 ALL SQL FILES PASSED VALIDATION!")
            print("✅ Ready for merge - please review and merge manually")
            sys.exit(0)
        else:
            print()
            print("❌ SOME SQL FILES FAILED VALIDATION:")
            for failed_file in failed_files:
                print(f"   • {failed_file}")
            print()
            print("❌ Please fix the issues before merging")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error during validation: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
