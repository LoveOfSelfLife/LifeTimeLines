from common.entity_store import EntityObject

class JournalDay (EntityObject):
    table_name="JournalDayTable"
    fields=["day_date_str", "items"]
    key_field="day_date_str"
    partition_value="jrnl"
    # items_list_field = "items"

    def __init__(self, d={}):
        super().__init__(d)
