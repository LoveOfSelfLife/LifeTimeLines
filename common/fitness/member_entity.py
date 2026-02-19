from common.blob_store import BlobStore
from common.entity_store import EntityObject, EntityStore
from werkzeug.utils import secure_filename
from common.fitness.member_schema import member_schema
from common.fitness.impersonation import get_impersonated_member_id

class FirstTimeUserException(Exception):
    def __init__(self):
        super().__init__("First time user")

class UnregisteredMemberException(Exception):
    def __init__(self):
        super().__init__("Unregistered member")

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

def get_user_profile(member_id):
    es = EntityStore()
    profile = es.get_item(MemberEntity({"id" : member_id}))
    return profile

def save_user_profile(profile, request_files):
    es = EntityStore()
    container_name = 'members'
    updated_profile = profile.copy()
    bs = BlobStore(container_name)
    # Handle profile photo upload
    if 'profile_photo' in request_files:
        file = request_files['profile_photo']
        if file and file.filename:
            filename = secure_filename(file.filename)
            # Upload the file to Azure Blob Storage
            # there will be an exception if the same image is uploaded twice, so lets add a timestamp to the filename to make it unique
            import time
            filename = f"{int(time.time())}_{filename}"
            bs.upload(file, filename)
            # Save the blob URL to the user's profile
            updated_profile["image_url"] = f"https://ltltablestorage.blob.core.windows.net/{container_name}/{filename}"
    es.upsert_item(MemberEntity(updated_profile))
    MembershipRegistry().refresh_members()
    return profile

# returns a dict with "id", "email", "name"
# "id" is the user id, "email" is the primary email, "name" is the name of the user
def get_member_detail_from_user_context(user_context):
    member_id = get_impersonated_member_id()
    if member_id:
        email = get_member_email_from_member_id(member_id)
        name = get_member_name_from_member_id(member_id)
        return { "id": member_id, "email": email, "name": name }

    member = dict()
    user = user_context.get('user')
    member['id'] = user.get('sub')
    member['email'] = user.get('emails')[0]
    if user.get('idp', None) == 'google.com':
        member['name'] = user.get('name', 'unknown')
    else:
        if user.get('name', None) != 'unknown':
            member['name'] = user.get('name', 'unknown')
        else:
            member['name'] = member.get('email', 'unknown')
    
    return member

def is_member_an_admin(member_id):
    # if a member is being impersonated, then the person doing the impersonation must be an admin, so we will return true in that case
    impersonated_member_id = get_impersonated_member_id()
    if impersonated_member_id:
        return True

    members_registry = MembershipRegistry()
    member = members_registry.get_member(member_id)
    return member.get('level') >= 10

def get_member_email_from_member_id(member_id):
    member_registry = MembershipRegistry()
    member = member_registry.get_member(member_id)
    return member.get('email', None)

def get_member_name_from_member_id(member_id):
    member_registry = MembershipRegistry()
    member = member_registry.get_member(member_id)
    return member.get('name', None)

def get_member_id_from_user_context(context):
    return get_member_detail_from_user_context(context).get('id', None)

def get_member_email_from_user_context(context):
    return get_member_detail_from_user_context(context).get('email', None)

def get_member_name_from_user_context(context):
    return get_member_detail_from_user_context(context).get('name', None)

class MembershipRegistry:
    _members = None

    def __init__(self):
        if not MembershipRegistry._members:
            self._load_members()

    def _load_members(self):
        MembershipRegistry._members = {m.get_key_value(): m for m in EntityStore().list_items(MemberEntity())}
        
    def check_if_member(self, member_id):
        return MembershipRegistry._members.get(member_id, None) is not None
    
    def add_member(self, member_id, member_email, member_name):
        member = { "id": member_id, "email": member_email, "name": member_name }
        member['level'] = 0
        EntityStore().upsert_item(MemberEntity(member))
        self._load_members()

    def get_member(self, member_id):
        return MembershipRegistry._members.get(member_id, None)
    
    def refresh_members(self):
        self._load_members()

    def verify_member_registration(self, member_id):
        if not self.check_if_member(member_id):
            raise FirstTimeUserException()
        member = self.get_member(member_id)
        if member.get('level', 0) == 0:
            raise UnregisteredMemberException()
        member['admin'] = member.get('level', 0) >= 10
        return member

