from identity.flask import Auth
import os
from dotenv import load_dotenv, find_dotenv

# Search upward from the working directory (the service folder), not from this
# file's directory (common/), which is what a bare load_dotenv() would use.
load_dotenv(find_dotenv(usecwd=True))

auth = Auth(
    None,
    authority=os.getenv("AUTHORITY"),
    client_id=os.getenv("B2C_CLIENT_ID"),
    client_credential=os.getenv("B2C_CLIENT_SECRET"),
    redirect_uri=os.getenv("REDIRECT_URI"),
    oidc_authority=os.getenv("OIDC_AUTHORITY"),
    b2c_tenant_name=os.getenv('B2C_TENANT_NAME'),
    b2c_signup_signin_user_flow=os.getenv('SIGNUPSIGNIN_USER_FLOW'),
    b2c_edit_profile_user_flow=os.getenv('EDITPROFILE_USER_FLOW'),
    b2c_reset_password_user_flow=os.getenv('RESETPASSWORD_USER_FLOW'),
)   

