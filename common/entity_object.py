from common.utils import IDGenerator

class EntityObject (dict):
    key_generator=IDGenerator.gen_id()
    table_name = None
    fields = None
    key_field=None
    partition_field=None
    partition_value=None
    items_list_field = None

    def __init__(self, d={}):
        dict.__init__(d)
        for k,v in d.items():
            self[k] = v

    def get_key_field(self):
        return type(self).key_field
    
    def get_key_value(self):
        return self[self.get_key_field()]

    def get_partition_field(self):
        return type(self).partition_field

    def get_partition_value(self):
        if type(self).partition_value:
            return type(self).partition_value
        return self[self.get_partition_field()]

    def get_static_partition_value(self):
        if type(self).partition_value:
            return type(self).partition_value
        return None

    def get_table_name(self):
        return type(self).table_name

    def get_fields(self):
        return type(self).fields
    
    def get_items_list_field(self):
        return type(self).items_list_field

    def key_generator(self):
        return type(self).key_generator

