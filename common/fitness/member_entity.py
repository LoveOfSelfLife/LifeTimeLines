from common.blob_store import BlobStore
from common.entity_store import EntityObject, EntityStore
from werkzeug.utils import secure_filename
from common.fitness.member_schema import member_schema

class MemberEntity (EntityObject):
    table_name="MemberTable"
    fields=["id", "name", "level", "short_name", "email", "mobile", "sms_consent", "email_consent", "image_url"]
    key_field="id"
    partition_value="member"
    schema = member_schema

    def __init__(self, d={}):
        super().__init__(d)

def get_members_list():
    es = EntityStore()
    members = []
    for m in es.list_items(MemberEntity()):
        members.append(m)
    return members

def get_user_profile(id):
    es = EntityStore()
    profile = es.get_item(MemberEntity({"id" : id}))
    return profile

def save_user_profile(profile, request_files):
    es = EntityStore()
    container_name = 'members'
    bs = BlobStore(container_name)
    # Handle profile photo upload
    if 'profile_photo' in request_files:
        file = request_files['profile_photo']
        if file and file.filename:
            filename = secure_filename(file.filename)
            # Upload the file to Azure Blob Storage
            bs.upload(file, filename)
            # Save the blob URL to the user's profile
            updated_profile = profile.copy()
            updated_profile["image_url"] = f"https://ltltablestorage.blob.core.windows.net/{container_name}/{filename}"
    es.upsert_item(MemberEntity(updated_profile))
    MembershipRegistry().refresh_members()
    return profile

# returns a dict with "id", "email", "name"
# "id" is the user id, "email" is the primary email, "name" is the name of the user
def get_member_detail_from_user_context(user_context):
    member = dict()
    user = user_context.get('user')
    member['id'] = user.get('sub')
    member['email'] = user.get('emails')[0]
    if user.get('idp', None) == 'google.com':
        member['name'] = user.get('name')
    else:
        if user.get('name', None) != 'unknown':
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
        MembershipRegistry._members = {m.get_key_value(): m for m in EntityStore().list_items(MemberEntity())}
        
    def check_if_member(self, member_id):
        return MembershipRegistry._members.get(member_id, None) is not None
    
    def add_member(self, member):
        member['level'] = 0
        EntityStore().upsert_item(MemberEntity(member))
        self._load_members()

    def get_member(self, member_id):
        return MembershipRegistry._members.get(member_id, None)
    
    def refresh_members(self):
        self._load_members()
    