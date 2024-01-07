from common.utils import IDGenerator

class EntityObject (dict):
    key_generator=IDGenerator.gen_id()
    table_name = None
    fields = None
    key_field=None
    partition_field=None
    partition_value=None

    def __init__(self, d):
        dict.__init__(d)
        for k,v in d.items():
            self[k] = v
        self.key_field = type(self).key_field
        self.partition_field = type(self).partition_field
        self.partition_value = type(self).partition_value
        self.table_name = type(self).table_name
        self.fields = type(self).fields

    def get_key_value(self):
        return self[self.key_field]
    
    def get_partition_value(self):
        if self.partition_value:
            return self.partition_value
        return self[self.partition_field]

    def get_table_name(self):
        return self.table_name

    def get_fields(self):
        return self.fields
