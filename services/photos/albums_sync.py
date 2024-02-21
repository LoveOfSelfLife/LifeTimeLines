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

    # def execute_album_sync(self):
    #     print('start albums synchronization')

    #     most_recent_item_time = None
        
    #     # list of all albums
    #     all_albums:list = list(self.photos_api.get_albums()) # has 'title' of album & 'id' of album

    #     # create a map of album title -> album id
    #     self.album_title_to_id_map = { a['title']: a['id'] for a in all_albums }
    #     self.album_id_to_title_map = { a['id']: a['title'] for a in all_albums }
        
    #     # list of all entities, some of which have photo albums
    #     person_entities = list(self.storage.list_items(PersonEntity())) # has 'id' & 'photos_album'
        
    #     # list of all album_ids that have been synced, along with the last sync time
    #     synced_albums = list(self.storage.list_items(AlbumSyncTime())) # has 'albumId' & 'lastSyncDateTime'
    #     albumId_to_syncTime_map = { a['albumId'] : a['lastSyncDateTime'] for a in synced_albums }

    #     # iterate through all personentities, get their album name and map to album id
    #     # then check if album id has already been synced
    #     # if it has been synced, get last sync time for that album id
    #     # then do a mitem sync of that album id, but only until you reach the last sync time, then stop
    #     # then update the album id's sync time and store it away
    #     # if album id has not been synced, then do a sync of all album items
    #     # then store away the album id with the time of the latest item in the album in the Symc_times table

    #     for e in person_entities:
    #         if 'photos_album' in e and e['photos_album']:
    #             album_id = self.album_title_to_id_map[e['photos_album']]

    #             album_sync_time_iso = albumId_to_syncTime_map.get(album_id, None)

    #             if album_sync_time_iso:
    #                 print(f"found album {e['photos_album']}")
    #             else:
    #                 print(f"new album {e['photos_album']}") 
    #             updated_album_sync_time_iso, num_items = self._sync_album_until_time(album_id, album_sync_time_iso, e['photos_album'])
                
    #             self.storage.upsert_item(AlbumSyncTime({"albumId": album_id,
    #                                                            "latestPhotoInAlbumTime" : updated_album_sync_time_iso}))
    def store_album_items(self, album_id, album_items):
        album_item_entities = [ AlbumItem({"mitemId": e['id'], 
                                          "albumId": album_id,
                                          "creationTime": e['creationTime']}) for e in album_items]
        self.storage.upsert_items(album_item_entities)

    def sync_album_items_incrementally(self, album_id, num_items, continuation_token=None):
        """
        Connects to the Google Photos API to retrieve the media items in an album incrementally, and to store those items in the entity store.

        the way this will work is that first time that the client call this (indirectly) they will provide the album_id and the number of items to synd in that call.
        so the first time this is called, client will only provide album_id and num_items. the continuation_token should be None.
        at the completion of the call, the response will contain list of items that were synced, as well as a continuation_token that will be provided in subsequent calls to this endpoint.
        that repeats until the continuation_token is None, at which point the client knows that all items have been synced.

        there are four scenarios in which this will be called:
        1. first time calling this when syncing a new album, which has never been synced before
        2. subequent calls to this when syncing a new album, which was previously never been synced before
        3. first time calling this when syncing an album that has been synced before
        4. subequent calls to this when syncing an album that has been synced before

        when this method is called, we will know if the album as been previously synced or not, by checking the AlbumSyncTime table.
        if the album has been previously synced, then the albumSyncTime table will have a record of the timestamp of the last item synced in the album, and we will use that timestamp to sync incrementally.
        if the album has not been previously synced, then the albumSyncTime table will not have such a record, and we will sync all items in the album.
        At the completion of the sync, we will store the timestamp of the last item synced in the album, to be used in future syncs to sync incrementally.

        so, when this methods is called, we check the albumSyncTime table to see if the scenario is 1 or 2, a new album sync, or if it is 3 or 4, a previously synced album.

        The trick is when to set the timestamp of the last item synced in the album.  This wil occur when we get an empty next_page_token in the response.
        We can't do it until after a full sync is complete, which will be
        after the last item is synced.  Then we need the timestamp of the item with the latest creation time.

        Args:
            album_id (str): ID of the album that we are retrieving.
            num_items (int): Number of media items to retrieve.
            next_page_token (str, optional): opaque token used to retrieve the next page of results. Defaults to None, which means it is the first call.
        """
        
        # first determine if album has been synced before
        synced_album_items_max_ts_iso = self.get_album_sync_ts_iso(album_id)

        if synced_album_items_max_ts_iso is None:
            # no, the album has not been synced before

            if continuation_token is None:
                # scenario 1. first time calling this when syncing a new album, which has never been synced before
                res = self.photos_api.get_album_items_incrementally(album_id, num_items, None, None)
                
                # capture the album items, the next page token, and the latest creation time of the newly retrieved items
                album_items_list = res['items']
                next_page_token = res['next_page_token']
                max_creation_time = res['max_creation_time']
            else:
                # scenario 2. subequent calls to this when syncing a new album, which was previously never been synced before
                # use the num_items from the continuation token, ignore what is passed in on subsequent calls
                # also use the max_creation_time from the continuation token, 

                num_items, max_creation_time, next_page_token = AlbumsSyncMgr.unpack(continuation_token)
                res = self.photos_api.get_album_items_incrementally(album_id, num_items, next_page_token, None)

                album_items_list = res['items']
                next_page_token = res['next_page_token']
        else:
            # yes, the album has been synced before
            cutoff_ts_dt = datetime.datetime.fromisoformat(synced_album_items_max_ts_iso)

            if continuation_token is None:
                # scenario 3. first time calling this when syncing an album that has been synced before
                res = self.photos_api.get_album_items_incrementally(album_id, num_items, None, cutoff_ts_dt)

                # capture the album items, the next page token, and the latest creation time of the newly retrieved items
                max_creation_time = res['max_creation_time']
                album_items_list = res['items']
                next_page_token = res['next_page_token']

            else:
                # scenario 4. subequent calls to this when syncing an album that has been synced before
                # use the num_items from the continuation token, ignore what is passed in on subsequent calls
                # also use the max_creation_time from the continuation token, 

                num_items, max_creation_time, next_page_token = AlbumsSyncMgr.unpack(continuation_token)
                res = self.photos_api.get_album_items_incrementally(album_id, num_items, next_page_token, cutoff_ts_dt)

                album_items_list = res['items']
                next_page_token = res['next_page_token']

        # store the album items in the entity store, regareless of how we got here
        if album_items_list:
            self.store_album_items(album_id, album_items_list)

        if next_page_token:
            # here we know there are more items to retrieve
            continuation_token = AlbumsSyncMgr.pack(num_items, max_creation_time, next_page_token)
            return { "items": album_items_list , "continuation_token": continuation_token }
        else:
            # when the next_page_token is None, then we know that we have synced all items in the album
            # record the max_creation_time in the AlbumSyncTime table, but only if we have a max_creation_time
            if max_creation_time:
                self.storage.upsert_item(AlbumSyncTime({"albumId": album_id,"latestPhotoInAlbumTime" : max_creation_time}))
            return { "items": album_items_list , "continuation_token": None }

    @staticmethod
    def pack(num_items, max_creation_time, next_page_token):
        import base64
        p = f"{num_items}|{max_creation_time}|{next_page_token}"
        pe = p.encode('utf-8')
        pe64 = base64.urlsafe_b64encode(pe)
        pe64s = pe64.decode('utf-8')
        return pe64s

    @staticmethod
    def unpack(continuation_token):
        import base64
        pe = continuation_token.encode('utf-8')
        pe64 = base64.urlsafe_b64decode(pe)
        pe = pe64.decode('utf-8')
        num_items, max_creation_time, next_page_token = pe.split('|', maxsplit=2)
        return (int(num_items), max_creation_time, next_page_token)

    # def sync_album(self, album_id):
    #     print(f'start sync_album({album_id})')
    #     album_sync_time_iso = self.get_album_sync_ts_iso(album_id)

    #     updated_album_sync_time_iso, num_items = self._sync_album_until_time(album_id, album_sync_time_iso)
        
    #     self.storage.upsert_item(AlbumSyncTime({"albumId": album_id,
    #                                                     "latestPhotoInAlbumTime" : updated_album_sync_time_iso}))
    #     return { "synced" : album_id, "numItemsSynced": num_items}

    def get_album_sync_ts_iso(self, album_id):
        album_sync_time_iso = None
        try:
            synced_album = self.storage.get_item(AlbumSyncTime({ "albumId": album_id}))
            album_sync_time_iso = synced_album.get('latestPhotoInAlbumTime', None)
        except:
            pass
        return album_sync_time_iso
    
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

    # def _sync_album_until_time(self, album_id, album_sync_time_iso, album_title=None):
    #     """
    #     Synchronizes the album until a specified time.

    #     Args:
    #         album_id (str): The ID of the album to synchronize.
    #         album_sync_time_iso (str): The ISO-formatted timestamp until which to synchronize the album.
    #         album_title (str, optional): The title of the album. Defaults to None.

    #     Returns:
    #         tuple: A tuple containing the most recent item's creation time in ISO format and the number of items stored.
    #     """
    #     mitems_to_store = []
    #     last_sync_time_dt = datetime.datetime.fromisoformat(album_sync_time_iso) if album_sync_time_iso else None
    #     most_recent_item_time_iso = None
    #     for album_mitem in self.photos_api.get_album_items(album_id):

    #         # each item will have 'id' and 'creationTime'
    #         id = album_mitem['id']
    #         ct_iso = album_mitem['creationTime']
    #         # save the creation time of the most recent item in the album
    #         if not most_recent_item_time_iso:
    #             most_recent_item_time_iso = ct_iso

    #         ct_dt = datetime.datetime.fromisoformat(ct_iso)
    #         if last_sync_time_dt and ct_dt <= last_sync_time_dt:
    #             break
    #         mitems_to_store.append(AlbumItem({"mitemId":id, "albumId":album_id, "creationTime":ct_iso}))
    #         if album_title:
    #             print(f"sync item {id} with creation time {ct_iso} for album {album_title}")

    #     self.storage.upsert_items(mitems_to_store)
    #     return most_recent_item_time_iso, len(mitems_to_store)

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
    # TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

    # ts_iso = "2024-01-04T23:39:29.4996176Z"
    # sync_times_tbl = EntityStore(AlbumSyncTime)
    # unfiltered = sync_times_tbl.list_items()
    # filtered = sync_times_tbl.list_items(f"(Timestamp lt datetime'{ts_iso}')")
    # # print(list(unfiltered))
    # print(list(filtered))
    # pass

    # asm = AlbumsSyncMgr()
    # asm.execute_album_sync()
    # asm.load_album_cache()
    

    # api = GooglePhotosApi(get_credentials())
    # start = {"year": 2020, "month": 1, "day": 1}
    # end = {"year": 2021, "month": 1, "day": 1}
    # mitems = api.get_media_items(start, end, 1000)
    # for m in mitems:
    #     mid = m['id']
    #     print(f"found item {mid} in albums: {list(asm.find_albums_contanining_mitem(mid))}")
