import datetime
from googlephotosapi import GooglePhotosApi
from common.google_credentials import get_credentials
from common.table_store import TableStore
from common.entity_store import EntityStore
from common.entities.albums import AlbumItem, AlbumSyncTime
from common.entities.person import PersonEntity

# MAX_DAYS_TO_GET_PER_REQUEST=30

class AlbumsSyncMgr ():
    def __init__(self):
        self.photos_api = GooglePhotosApi(get_credentials())
        self.storage = EntityStore()

    def execute_album_sync(self):
        print('start albums synchronization')

        most_recent_item_time = None
        
        # list of all albums
        all_albums:list = list(self.photos_api.get_albums()) # has 'title' of album & 'id' of album

        # create a map of album title -> album id
        self.album_title_to_id_map = { a['title']: a['id'] for a in all_albums }
        self.album_id_to_title_map = { a['id']: a['title'] for a in all_albums }
        
        # list of all entities, some of which have photo albums
        person_entities = list(self.storage.list_items(PersonEntity())) # has 'id' & 'photos_album'
        
        # list of all album_ids that have been synced, along with the last sync time
        synced_albums = list(self.storage.list_items(AlbumSyncTime())) # has 'albumId' & 'lastSyncDateTime'
        albumId_to_syncTime_map = { a['albumId'] : a['lastSyncDateTime'] for a in synced_albums }

        # iterate through all personentities, get their album name and map to album id
        # then check if album id has already been synced
        # if it has been synced, get last sync time for that album id
        # then do a mitem sync of that album id, but only until you reach the last sync time, then stop
        # then update the album id's sync time and store it away
        # if album id has not been synced, then do a sync of all album items
        # then store away the album id with the time of the latest item in the album in the Symc_times table

        for e in person_entities:
            if 'photos_album' in e and e['photos_album']:
                album_id = self.album_title_to_id_map[e['photos_album']]

                album_sync_time_iso = albumId_to_syncTime_map.get(album_id, None)

                if album_sync_time_iso:
                    print(f"found album {e['photos_album']}")
                else:
                    print(f"new album {e['photos_album']}") 
                updated_album_sync_time_iso, num_items = self._sync_album_until_time(album_id, album_sync_time_iso, e['photos_album'])
                
                self.storage.upsert_item(AlbumSyncTime({"albumId": album_id,
                                                               "latestPhotoInAlbumTime" : updated_album_sync_time_iso}))

    def sync_album(self, album_id):
        print(f'start sync_album({album_id})')
        album_sync_time_iso = None
        try:
            synced_album = self.storage.get_item(AlbumSyncTime({ "albumId": album_id}))

            album_sync_time_iso = synced_album.get('latestPhotoInAlbumTime', None)
        except:
            pass

        updated_album_sync_time_iso, num_items = self._sync_album_until_time(album_id, album_sync_time_iso)
        
        self.storage.upsert_item(AlbumSyncTime({"albumId": album_id,
                                                        "latestPhotoInAlbumTime" : updated_album_sync_time_iso}))
        return { "synced" : album_id, "numItemsSynced": num_items}
    
    def get_actor_entity_albums(self):
        # list of all albums
        all_albums:list = list(self.photos_api.get_albums()) # has 'title' of album & 'id' of album

        # create a map of album title -> album id
        self.album_title_to_id_map = { a['title']: a['id'] for a in all_albums }
        # self.album_id_to_title_map = { a['id']: a['title'] for a in all_albums }        
        
        # list of all album_ids that have been synced, along with the last sync time
        synced_albums = list(self.storage.list_items(AlbumSyncTime())) # has 'albumId' & 'lastSyncDateTime'
        albumId_to_syncTime_map = { a['albumId'] : a['latestPhotoInAlbumTime'] for a in synced_albums }

        # iterate through all personentities, get their album name and map to album id
        # then we return the album_id & latestPhotoInAlbumTime

        person_entities = list(self.storage.list_items(PersonEntity())) # has 'id' & 'photos_album'
        for e in person_entities:
            if 'photos_album' in e and e['photos_album']:
                albumName = e['photos_album']
                if albumName in self.album_title_to_id_map:
                    album_id = self.album_title_to_id_map[albumName]
                    album_sync_time_iso = albumId_to_syncTime_map.get(album_id,None)
                    yield { "albumId": album_id, "albumName": albumName, "latestPhotoInAlbumTime": album_sync_time_iso}

    def _sync_album_until_time(self, album_id, album_sync_time_iso, album_title=None):
        """
        Synchronizes the album until a specified time.

        Args:
            album_id (str): The ID of the album to synchronize.
            album_sync_time_iso (str): The ISO-formatted timestamp until which to synchronize the album.
            album_title (str, optional): The title of the album. Defaults to None.

        Returns:
            tuple: A tuple containing the most recent item's creation time in ISO format and the number of items stored.
        """
        mitems_to_store = []
        last_sync_time_dt = datetime.datetime.fromisoformat(album_sync_time_iso) if album_sync_time_iso else None
        most_recent_item_time_iso = None
        for album_mitem in self.photos_api.get_album_items(album_id):

            # each item will have 'id' and 'creationTime'
            id = album_mitem['id']
            ct_iso = album_mitem['creationTime']
            # save the creation time of the most recent item in the album
            if not most_recent_item_time_iso:
                most_recent_item_time_iso = ct_iso

            ct_dt = datetime.datetime.fromisoformat(ct_iso)
            if last_sync_time_dt and ct_dt <= last_sync_time_dt:
                break
            mitems_to_store.append(AlbumItem({"mitemId":id, "albumId":album_id, "creationTime":ct_iso}))
            if album_title:
                print(f"sync item {id} with creation time {ct_iso} for album {album_title}")

        self.storage.upsert_items(mitems_to_store)
        return most_recent_item_time_iso, len(mitems_to_store)

    def load_album_cache(self):
        album_items = self.storage.list_items(AlbumItem())
        (self.album_item_map, self.album_item_set) = self._load_album_items_cache(album_items)

    def find_albums_contanining_mitem(self, mitem):
        for a in self.album_item_map.keys():
            if mitem in self.album_item_set[a]:
                yield self.album_id_to_title_map[a]

    def _load_album_items_cache(self, album_items):
        album_items_map = {}
        album_items_set = {}

        for ai in album_items:
            # "mitemId", "albumId", "creationTime"
            mitemId = ai["mitemId"]
            albumId = ai["albumId"]
            creationTime_iso = ai["creationTime"]
            creationTime_dt = datetime.datetime.fromisoformat(creationTime_iso)

            if not album_items_map.get(albumId, None):
                album_items_map[albumId] = list()
                album_items_set[albumId] = set()                
            album_items_map[albumId].append((mitemId, creationTime_dt))
            album_items_set[albumId].add(mitemId)
            
        for k in album_items_map.keys():
            item_pair_list = sorted(album_items_map[k], key=lambda x : x[1], reverse=True)
            album_items_map[k] = item_pair_list

        return album_items_map, album_items_set
    


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

    # ts_iso = "2024-01-04T23:39:29.4996176Z"
    # sync_times_tbl = EntityStore(AlbumSyncTime)
    # unfiltered = sync_times_tbl.list_items()
    # filtered = sync_times_tbl.list_items(f"(Timestamp lt datetime'{ts_iso}')")
    # # print(list(unfiltered))
    # print(list(filtered))
    # pass

    asm = AlbumsSyncMgr()
    asm.execute_album_sync()
    asm.load_album_cache()
    

    api = GooglePhotosApi(get_credentials())
    start = {"year": 2020, "month": 1, "day": 1}
    end = {"year": 2021, "month": 1, "day": 1}
    mitems = api.get_media_items(start, end, 1000)
    for m in mitems:
        mid = m['id']
        print(f"found item {mid} in albums: {list(asm.find_albums_contanining_mitem(mid))}")
