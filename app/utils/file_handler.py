import os
import uuid
from io import BytesIO
import base64

ALLOWED_EXTENSIONS     = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_DOC_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}


def allowed_file(filename, extensions=None):
    if extensions is None:
        extensions = ALLOWED_EXTENSIONS
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in extensions
    )


def _get_upload_dir(subfolder):
    """
    Returns absolute path to upload directory.
    Saves to  <project>/app/static/uploads/<subfolder>/
    Flask serves app/static/ at /static/ automatically.
    """
    from flask import current_app
    # current_app.root_path == .../event_management/app
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def save_uploaded_file(file, subfolder, max_size=(1200, 1200)):
    """Save uploaded image. Returns 'uploads/subfolder/filename.ext'"""
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        return None

    try:
        target_dir = _get_upload_dir(subfolder)
    except Exception as e:
        print(f'Upload dir error: {e}')
        return None

    ext      = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(target_dir, filename)

    try:
        from PIL import Image
        file.stream.seek(0)
        img = Image.open(file.stream)
        img = img.convert('RGB')
        img.thumbnail(max_size, Image.LANCZOS)
        img.save(filepath, quality=85, optimize=True)
    except Exception as e:
        print(f'PIL error: {e} — saving raw')
        try:
            file.stream.seek(0)
            with open(filepath, 'wb') as f:
                f.write(file.stream.read())
        except Exception as e2:
            print(f'Raw save error: {e2}')
            return None

    print(f'✅ Saved image: {filepath}')
    return f"uploads/{subfolder}/{filename}"


def save_base64_image(base64_str, subfolder, prefix='ai_'):
    """Save base64 image. Returns 'uploads/subfolder/filename.jpg'"""
    try:
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
        image_data = base64.b64decode(base64_str)
        target_dir = _get_upload_dir(subfolder)
        filename   = f"{prefix}{uuid.uuid4().hex}.jpg"
        filepath   = os.path.join(target_dir, filename)
        from PIL import Image
        img = Image.open(BytesIO(image_data)).convert('RGB')
        img.save(filepath, quality=85)
        return f"uploads/{subfolder}/{filename}"
    except Exception as e:
        print(f'base64 save error: {e}')
        return None


def save_receipt(file):
    """Save receipt (image or PDF). Returns 'uploads/receipts/filename'"""
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename, ALLOWED_DOC_EXTENSIONS):
        return None

    try:
        target_dir = _get_upload_dir('receipts')
    except Exception:
        return None

    ext      = file.filename.rsplit('.', 1)[1].lower()
    filename = f"receipt_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(target_dir, filename)

    if ext == 'pdf':
        file.save(filepath)
    else:
        try:
            from PIL import Image
            file.stream.seek(0)
            img = Image.open(file.stream).convert('RGB')
            img.thumbnail((1200, 1200), Image.LANCZOS)
            img.save(filepath, quality=85)
        except Exception:
            file.stream.seek(0)
            file.save(filepath)

    return f"uploads/receipts/{filename}"


def delete_file(relative_path):
    """Delete file given 'uploads/designs/abc.jpg'"""
    if not relative_path:
        return False
    try:
        from flask import current_app
        full_path = os.path.join(current_app.root_path, 'static', relative_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    except Exception as e:
        print(f'Delete error: {e}')
    return False


def save_thumbnail(image_path, subfolder, size=(300, 300)):
    """Create thumbnail from existing image."""
    try:
        from flask import current_app
        from PIL import Image
        full_path = os.path.join(current_app.root_path, 'static', image_path)
        if not os.path.exists(full_path):
            return None
        img        = Image.open(full_path).convert('RGB')
        img.thumbnail(size, Image.LANCZOS)
        filename   = 'thumb_' + os.path.basename(full_path)
        target_dir = _get_upload_dir(subfolder)
        thumb_path = os.path.join(target_dir, filename)
        img.save(thumb_path, quality=80)
        return f"uploads/{subfolder}/{filename}"
    except Exception as e:
        print(f'Thumbnail error: {e}')
        return None
