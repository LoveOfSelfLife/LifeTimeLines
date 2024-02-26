import unittest
from unittest.mock import MagicMock
from datetime import datetime
from services.photos.albums_sync import AlbumSync

class TestAlbumSync(unittest.TestCase):

    def setUp(self):
        self.album_sync = AlbumSync()
        self.album_sync.photos_api = MagicMock()
        self.album_sync.storage = MagicMock()

    def test_sync_album_until_time(self):
        album_id = "album123"
        album_sync_time_iso = "2022-01-01T00:00:00Z"
        album_title = "Test Album"

        # Mock the response from the photos API
        album_items = [
            {"id": "item1", "creationTime": "2022-01-01T10:00:00Z"},
            {"id": "item2", "creationTime": "2022-01-02T12:00:00Z"},
            {"id": "item3", "creationTime": "2022-01-03T15:00:00Z"}
        ]
        self.album_sync.photos_api.get_album_items.return_value = album_items

        # Mock the storage upsert_items method
        self.album_sync.storage.upsert_items.return_value = None

        # Call the method under test
        result = self.album_sync._sync_album_until_time(album_id, album_sync_time_iso, album_title)

        # Assert the expected result
        expected_most_recent_item_time_iso = "2022-01-03T15:00:00Z"
        expected_num_items_stored = 3
        self.assertEqual(result, (expected_most_recent_item_time_iso, expected_num_items_stored))

        # Assert that the photos API was called with the correct arguments
        self.album_sync.photos_api.get_album_items.assert_called_once_with(album_id)

        # Assert that the storage upsert_items method was called with the correct arguments
        expected_mitems_to_store = [
            {"mitemId": "item1", "albumId": album_id, "creationTime": "2022-01-01T10:00:00Z"},
            {"mitemId": "item2", "albumId": album_id, "creationTime": "2022-01-02T12:00:00Z"},
            {"mitemId": "item3", "albumId": album_id, "creationTime": "2022-01-03T15:00:00Z"}
        ]
        self.album_sync.storage.upsert_items.assert_called_once_with(expected_mitems_to_store)

if __name__ == '__main__':
    unittest.main()