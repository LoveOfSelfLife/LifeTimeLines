import unittest
from datetime import date
from common.parsers.journal.daydata import DayData, DayItem

class TestDayData(unittest.TestCase):

    def setUp(self):
        self.day_data = DayData(2023, 10, 5)

    def test_get_date_str(self):
        self.assertEqual(self.day_data.get_date_str(), '2023-10-05')

    # def test_get_date_int(self):
    #     self.assertEqual(self.day_data.get_date_int(), 12310500000)

    def test_get_day_of_week(self):
        self.assertEqual(self.day_data.get_day_of_week(), 4)  # Thursday

    def test_get_day_of_week_str(self):
        self.assertEqual(self.day_data.get_day_of_week_str(), 'thu')

    def test_get_week_of_year(self):
        self.assertEqual(self.day_data.get_week_of_year(), 40)

class TestDayItem(unittest.TestCase):

    def setUp(self):
        self.day_item = DayItem()

    def test_set_and_get_time(self):
        self.day_item.set_time("10:30AM")
        self.assertEqual(self.day_item.time, "10:30AM")

    def test_set_and_get_type(self):
        self.day_item.set_type("KEY")
        self.assertEqual(self.day_item.type, "KEY")

    def test_add_text(self):
        self.day_item.append_text("Sample text")
        self.assertIn("Sample text", self.day_item.text_items)

    def test_set_item_num(self):
        self.assertEqual(self.day_item.set_item_num(1), 1)
        self.assertEqual(self.day_item.item_offset, 1)

    def test_set_and_get_key(self):
        self.day_item.set_key("SampleKey")
        self.assertEqual(self.day_item.key, "SampleKey")

    def test_set_and_get_val(self):
        self.day_item.set_val("SampleVal")
        self.assertEqual(self.day_item.key_val, "SampleVal")

    def test_set_key_val_param(self):
        self.day_item.set_key_val_param([("param1", "value1"), ("param2", "value2")])
        self.assertEqual(self.day_item.key_val_list, [("param1", "value1"), ("param2", "value2")])

    def test_set_hour_min_ampm(self):
        self.day_item.set_hour(10)
        self.day_item.set_min(30)
        self.day_item.set_am_pm("AM")
        self.assertEqual(self.day_item.hour, 10)
        self.assertEqual(self.day_item.min, 30)
        self.assertEqual(self.day_item.am_pm, "AM")

if __name__ == '__main__':
    unittest.main()
