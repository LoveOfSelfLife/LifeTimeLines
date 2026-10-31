"""
Rebuilds the exercise analytics SQLite db for one member (or all members) from the entity store.

Run from this folder (so .env is found), with the repo root on PYTHONPATH:
    $env:PYTHONPATH = "..\..\.."
    python rebuild_analytics_db.py --member-id <member id> --db .\workouts.sqlite
    python rebuild_analytics_db.py --all --db .\workouts.sqlite
"""
import argparse
import os

from dotenv import load_dotenv

from common.blob_store import BlobStore
from common.entity_store import EntityStore, instatiate_all_entity_objects
from common.fitness import exercise_analytics_db as adb
# from common.fitness.member_entity import MemberEntity
from common.table_store import TableStore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--member-id')
    parser.add_argument('--all', action='store_true', help='rebuild every member')
    parser.add_argument('--db', default=None, help='sqlite file to write (default: the share path)')
    args = parser.parse_args()
    if not args.member_id and not args.all:
        parser.error('give --member-id or --all')

    load_dotenv('.env')
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING'))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING'))
    instatiate_all_entity_objects()

    member_ids = [args.member_id] if args.member_id else [m.get('id') for m in EntityStore().list_items(MemberEntity())]
    conn = adb.connect(args.db)
    for member_id in member_ids:
        workouts, facts = adb.rebuild_member_from_entity_store(conn, member_id)
        print(f"{member_id}: {workouts} workouts, {facts} exercise rows")
    print(f"db: {args.db or adb.get_db_path()}")


if __name__ == '__main__':
    main()
