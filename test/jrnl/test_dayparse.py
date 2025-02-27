import unittest
from datetime import date
from common.parsers.journal.daydata import DayData, DayItem, parse_jrnl_data, DayItem

class TestDayParse(unittest.TestCase):

    def setUp(self):
        self.day_data = DayData(2023, 10, 5)

    def test_keys(self):
        KEYS_FILE='local/keys.txt'
        with open(KEYS_FILE) as f:
            days = parse_jrnl_data(f)
            for day in days:
                for item in day.items:
                    print(item)




if __name__ == '__main__':
    unittest.main()
