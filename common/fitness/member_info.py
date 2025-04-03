from common.entity_store import EntityStore
from common.fitness.members import MemberEntity

def get_user_profile(id):
    es = EntityStore()
    profile = es.get_item(MemberEntity({"id" : id}))
    return profile

def save_user_profile(profile):
    es = EntityStore()
    es.upsert_item(MemberEntity(profile))
    MembershipRegistry().refresh_members()
    return profile

def get_user_info_from_token(token):
    member = dict()
    user = token.get('user')
    member['id'] = user.get('sub')
    member['email'] = user.get('emails')[0]
    if user.get('idp', None) == 'google.com':
        member['name'] = user.get('name')
    else:
        if user.get('name', None) != 'uknown':
            member['name'] = user.get('name')
        else:
            member['name'] = member['email']
    
    return member

class MembershipRegistry:
    _members = None

    def __init__(self):
        if not MembershipRegistry._members:
            self._load_members()

    def _load_members(self):
        MembershipRegistry._members = dict()
        for m in EntityStore().list_items(MemberEntity()):
            member_id = m.get_key_value()
            MembershipRegistry._members[member_id] = m
        
    def check_if_member(self, member_id):
        return MembershipRegistry._members.get(member_id) is not None
    
    def add_member(self, member):
        member['level'] = 0
        EntityStore().upsert_item(MemberEntity(member))
        self._load_members()

    def get_member(self, member_id):
        return MembershipRegistry._members.get(member_id)
    
    def refresh_members(self):
        self._load_members()
    