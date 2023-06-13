
def sync_mitems():
    return [ "sync_mitems" ]
def sync_entities():
    return [ "sync_entities" ]
def curate_mitems():
    return [ "curate_mitems" ]
def index_mitems():
    return [ "index_mitems" ]

PHOTOS_TASKS = [
                {
                    "task_name": "sync-mitems",
                    "do_task": sync_mitems,
                    "get_status": sync_mitems
                },
                {
                    "task_name": "sync-entities",
                    "do_task": sync_entities,
                    "get_status": sync_mitems
                },
                {
                    "task_name": "curate-mitems",
                    "do_task": curate_mitems,
                    "get_status": sync_mitems
                },
                {
                    "task_name": "index-mitems",
                    "do_task": index_mitems,
                    "get_status": sync_mitems
                }
            ]

