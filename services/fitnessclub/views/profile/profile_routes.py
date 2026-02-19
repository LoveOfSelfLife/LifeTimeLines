from flask import Blueprint, redirect, render_template, request, url_for
from common.fitness.hx_common import hx_render_template
from common.fitness.member_entity import get_member_detail_from_user_context, get_user_profile, save_user_profile
bp = Blueprint('profile', __name__, template_folder='templates')
from auth import auth

@bp.route('/')
@auth.login_required
def profile(context=None):
    profile = {
        "id": "123456",
        "name": "John Doe",
        "shortname": "JD",
        "email": "jd@mail.com",
        "mobile": "123-456-7890",
        "sms_consent": "agree" }
    
    id = get_member_detail_from_user_context(context).get('id')

    profile = get_user_profile(id)

    return hx_render_template('profile_nav.html', 
                              context=context, 
                              profile=profile,
                              hx_push_url="/profile/update",
                              update_url="/profile/update")
@bp.route('/profile2')
@auth.login_required
def profile2(context=None):
    profile = {
        "id": "123456",
        "name": "John Doe",
        "shortname": "JD",
        "email": "jd@mail.com",
        "mobile": "123-456-7890",
        "sms_consent": "agree" }
    
    id = get_member_detail_from_user_context(context).get('id')

    profile = get_user_profile(id)

    return hx_render_template('profile2.html', 
                              context=context, 
                              profile=profile,
                              hx_push_url="/profile/update",
                              update_url="/profile/update")

@bp.route('/settings')
@auth.login_required
def settings(context=None):

    return hx_render_template('settings.html', 
                              context=context, 
                              profile=profile,
                              hx_push_url="/profile/update",
                              update_url="/profile/update")

@bp.route('/update', methods=['POST'])
@auth.login_required
def update_profile(context=None):
    import io
    import base64
    from werkzeug.datastructures import FileStorage
    
    print(f"Request: {request.form}")
    
    # Handle captured photo data from camera
    files = request.files.copy()
    captured_photo_data = request.form.get('captured_photo_data', '')
    
    if captured_photo_data:
        try:
            # Parse the base64 data (remove data:image/jpeg;base64, prefix)
            header, encoded = captured_photo_data.split(',', 1)
            image_data = base64.b64decode(encoded)
            
            # Create a file-like object from the decoded image data
            image_io = io.BytesIO(image_data)
            
            # Create a FileStorage object (mimicking file upload)
            captured_file = FileStorage(
                stream=image_io,
                filename=f'profile_selfie_{context.get("user", {}).get("sub", "unknown")}.jpg',
                content_type='image/jpeg'
            )
            
            # Add the captured photo to files for processing
            files['profile_photo'] = captured_file
            
        except Exception as e:
            print(f"Error processing captured photo: {e}")

    profile = save_user_profile(request.form, files)
    return redirect("/")
  
