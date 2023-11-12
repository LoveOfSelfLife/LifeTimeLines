from common.utils import IDGenerator

class EntityObject (dict):
    key_generator=IDGenerator.gen_id()
    partition_field=None
    partition_value=None

    def __init__(self, d):
        dict.__init__(d)
        for k,v in d.items():
            self[k] = v