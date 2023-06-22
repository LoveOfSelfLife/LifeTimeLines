
import datetime
from common.utils import generate_unique_id
from googlephotosapi import GooglePhotosApi
from common.google_credentials import get_credentials
from common.tables import TableStore
from common.date_ranges_mgr import add_range, load_date_ranges_from_storage, get_unexplored_date_range
from common.date_ranges_mgr import break_up_date_range_into_chunks
from common.date_ranges_mgr import coaslesc_ranges
from common.entity_store import EntityStore
from common.entities.photos import PhotosDateRanges
from common.entities.albums import AlbumItem, SyncTime
from common.entities.person import PersonEntity

MAX_DAYS_TO_GET_PER_REQUEST=30

class AlbumsSyncMgr ():
    def __init__(self):
        self.api = GooglePhotosApi(get_credentials())
        self.sync_times_tbl = EntityStore(SyncTime)
        self.album_items_tbl = EntityStore(AlbumItem)
        self.person_entity_tbl = EntityStore(PersonEntity)

    def _convert_mitems_to_entities(self, mitems):
        return [ {"RowKey": e['id'], "PartitionKey": "media_item", "creationTime": e['creationTime']} for e in mitems]

    def execute_album_sync(self):
        print('start albums synchronization')

        most_recent_item_time = None
        
        # list of all albums
        all_albums:list = self.api.get_albums() # has 'title' of album & 'id' of album

        # create a map of album title -> album id
        album_map = { a['title']: a['id'] for a in all_albums }
        
        # list of all entities, some of which have photo albums
        person_entities = list(self.person_entity_tbl.list_items()) # has 'id' & 'photos_album'
        
        # list of all album_ids that have been synced, along with the last sync time
        synced_albums = list(self.sync_times_tbl.list_items()) # has 'albumId' & 'lastSyncDateTime'
        sync_map = { a['albumId'] : a['lastSyncDateTime'] for a in synced_albums }

        # iterate through all personentities, get their album name and map to album id
        # then check if album id has already been synced
        # if it has been synced, get last sync time for that album id
        # then do a mitem sync of that album id, but only until you reach the last sync time, then stop
        # then update the album id's sync time and store it away
        # if album id has not been synced, then do a sync of all album items
        # then store away the album id with the time of the latest item in the album in the Symc_times table

        for e in person_entities:
            if 'photos_album' in e and e['photos_album']:
                album_id = album_map[e['photos_album']]
                last_sync_time = None
                if album_id in sync_map.keys():
                    last_sync_time = sync_map[album_id]
                    print(f"found album {e['photos_album']}")
                else:
                    print(f"new album {e['photos_album']}") 
                new_sync_time = self.sync_album_until_time(album_id, e['photos_album'], last_sync_time)
                
                self.sync_times_tbl.upsert_item(SyncTime({"albumId": album_id, 
                                                          "lastSyncDateTime" : new_sync_time}))

    def sync_album_until_time(self, album_id, album_title, last_sync_time):
        mitems_to_store = []
        last_sync_time_dt = datetime.datetime.fromisoformat(last_sync_time) if last_sync_time else None
        most_recent_item_time = None
        for album_mitem in self.api.get_album_items(album_id):

            # each item will have 'id' and 'creationTime'
            id = album_mitem['id']
            ct = album_mitem['creationTime']
            # save the creation time of the most recent item in the album
            if not most_recent_item_time:
                most_recent_item_time = ct

            ct_dt = datetime.datetime.fromisoformat(ct)
            if last_sync_time_dt and ct_dt <= last_sync_time_dt:
                break
            mitems_to_store.append(AlbumItem({"mitemId":id, "albumId":album_id, "creationTime":ct}))
            print(f"sync item {id} with creation time {ct} for album {album_title}")

        self.album_items_tbl.upsert_items(mitems_to_store)
        return most_recent_item_time

    def _load_album_items(self, album_items):
        album_items_map = {}

        for ai in album_items:
            # "mitemId", "albumId", "creationTime"
            mitemId = ai["mitemId"]
            albumId = ai["albumId"]
            creationTime = ai["creationTime"]
            creationTime_dt = datetime.datetime.fromisoformat(creationTime)

            if not album_items_map.get(albumId, None):
                album_items_map[albumId] = []
            album_items_map[albumId].append((mitemId, creationTime_dt))
            
        for k in album_items_map.keys():
            item_pair_list = sorted(album_items_map[k], key=lambda x : x[1], reverse=True)
            album_items_map[k] = item_pair_list

        return album_items_map
    
    def load_album_cache(self):
        sync_times = self.sync_times_tbl.list_items()
        album_items = self.album_items_tbl.list_items()
        album_item_map = self._load_album_items(album_items)
        return album_item_map
    



if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

    asm = AlbumsSyncMgr()
    asm.execute_album_sync()
    cache = asm.load_album_cache()
    print(cache)



