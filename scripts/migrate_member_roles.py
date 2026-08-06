#!/usr/bin/env python3
"""
Migration utility to add 'role' field to existing MemberEntity records.
This script sets the default role to 'client' for all existing members.

Usage:
python scripts/migrate_member_roles.py
"""

import sys
import os

from dotenv import load_dotenv

from common.table_store import TableStore
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.entity_store import EntityStore
from common.fitness.member_entity import MemberEntity, get_members_list


def init():
    load_dotenv('fitnessclub/.env')
    print(f"Current working directory: {os.getcwd()}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))


def migrate_member_roles():
    """
    Add role field to existing members, defaulting to 'client'
    """
    print("Starting member role migration...")
    
    es = EntityStore()
    members = get_members_list()
    
    updated_count = 0
    already_updated_count = 0
    
    for member in members:
        if 'role' not in member or not member.get('role'):
            # Add role field with default value
            member['role'] = 'client'
            
            # Update the member entity
            member_entity = MemberEntity(member)
            es.upsert_item(member_entity)
            
            print(f"Updated member {member.get('name', member.get('id'))} - set role to 'client'")
            updated_count += 1
        else:
            print(f"Member {member.get('name', member.get('id'))} already has role: {member.get('role')}")
            already_updated_count += 1
    
    print(f"\nMigration complete!")
    print(f"Members updated: {updated_count}")
    print(f"Members already with role: {already_updated_count}")
    print(f"Total members: {len(members)}")
    
    if updated_count > 0:
        print(f"\nNOTE: Updated members will have role='client'. Admin users still keep their admin privileges via level >= 10.")

def validate_migration():
    """
    Validate that all members now have a role field
    """
    print("\nValidating migration...")
    
    members = get_members_list()
    missing_role_count = 0
    
    for member in members:
        if 'role' not in member or not member.get('role'):
            print(f"WARNING: Member {member.get('name', member.get('id'))} still missing role field!")
            missing_role_count += 1
        else:
            role = member.get('role')
            level = member.get('level', 0)
            admin_status = "Admin" if level >= 10 else "Regular"
            print(f"✓ {member.get('name', member.get('id'))}: role={role}, {admin_status}")
    
    if missing_role_count == 0:
        print("\n✅ Migration validation successful! All members have role field.")
    else:
        print(f"\n❌ Migration validation failed! {missing_role_count} members missing role field.")
    
    return missing_role_count == 0

if __name__ == "__main__":
    try:
        init()

        # Perform migration
        migrate_member_roles()
        
        # Validate migration
        success = validate_migration()
        
        if success:
            print("\n🎉 Role migration completed successfully!")
        else:
            print("\n💥 Migration had issues. Please review the output above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)