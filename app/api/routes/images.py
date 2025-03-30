import uuid
from typing import Any, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.models import Image, ImageCreate, ImagePublic, ImagesPublic, ImageUpdate, Message, User
from app.services.supabase_storage import supabase_storage

router = APIRouter(prefix="/images", tags=["images"])

@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...)
) -> Any:
    """
    Upload an image to Supabase Storage without authentication.
    """
    # Check file type
    content_type = file.content_type
    if not content_type or not content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )
    
    try:
        # Make sure we're at the beginning of the file
        await file.seek(0)
        
        # Upload to Supabase
        file_url = await supabase_storage.upload_file(
            file=file.file,
            content_type=content_type
        )
        
        return {
            "success": True,
            "message": "Image uploaded successfully",
            "url": file_url
        }
    except Exception as e:
        error_msg = str(e)
        
        # Provide more detailed error information
        details = {
            "success": False,
            "message": f"Error uploading image: {error_msg}",
            "supabase_url": settings.SUPABASE_URL,
            "bucket_name": settings.SUPABASE_BUCKET,
            "troubleshooting": "Make sure you have created the bucket and configured RLS policies correctly."
        }
        
        # Add specific troubleshooting advice based on the error
        if "new row violates row-level security policy" in error_msg or "403" in error_msg:
            details["troubleshooting"] = (
                "This is a permissions issue. You need to configure RLS policies in Supabase. "
                "Go to Storage > Policies and create a policy that allows INSERT operations. "
                "For testing, you can set the policy to 'true' to allow all operations."
            )
        elif "bucket" in error_msg.lower() and "not found" in error_msg.lower():
            details["troubleshooting"] = (
                f"The bucket '{settings.SUPABASE_BUCKET}' was not found. "
                "Make sure you have created it in the Supabase dashboard with exactly this name."
            )
            
        return details

@router.get("/supabase-status")
async def get_supabase_status() -> Any:
    """
    Get Supabase status information to help diagnose issues.
    """
    try:
        # Check Supabase connection
        buckets = supabase_storage.supabase.storage.list_buckets()
        bucket_names = [bucket.name for bucket in buckets]
        
        # Try to access the bucket directly
        bucket_accessible = False
        bucket_details = None
        try:
            # List files in bucket
            files = supabase_storage.supabase.storage.from_(supabase_storage.bucket_name).list()
            bucket_accessible = True
            bucket_details = {
                "file_count": len(files),
                "files": files[:5]  # Show first 5 files
            }
        except Exception as e:
            bucket_details = {
                "error": f"Could not list files: {str(e)}"
            }
        
        # Check if our bucket exists in the list
        bucket_visible = supabase_storage.bucket_name in bucket_names
        
        return {
            "success": True,
            "supabase_url": settings.SUPABASE_URL,
            "bucket_name": supabase_storage.bucket_name,
            "buckets_visible": bucket_names,
            "bucket_visible_in_list": bucket_visible,
            "bucket_accessible": bucket_accessible,
            "bucket_details": bucket_details,
            "rls_status": "The bucket exists but is not visible in the list due to RLS policies" if (bucket_accessible and not bucket_visible) else "Normal",
            "message": "Supabase connection successful"
        }
    except Exception as e:
        return {
            "success": False,
            "supabase_url": settings.SUPABASE_URL,
            "bucket_name": supabase_storage.bucket_name,
            "message": f"Error connecting to Supabase: {str(e)}"
        }

@router.get("/")
async def list_images() -> Any:
    """
    List all images in the Supabase bucket.
    """
    try:
        # List files in bucket
        files = supabase_storage.supabase.storage.from_(supabase_storage.bucket_name).list()
        
        # Convert to list of image URLs
        images = []
        for file in files:
            # Try to create a signed URL with a long expiration time
            try:
                # Create a signed URL that expires in 10 years (effectively permanent)
                signed_url_data = supabase_storage.supabase.storage.from_(supabase_storage.bucket_name).create_signed_url(
                    path=file["name"],
                    expires_in=315360000  # 10 years in seconds
                )
                
                if signed_url_data and 'signedURL' in signed_url_data:
                    file_url = signed_url_data['signedURL']
                    print(f"Generated signed URL for list: {file_url}")
                else:
                    # Fallback to public URL
                    file_url = supabase_storage.supabase.storage.from_(supabase_storage.bucket_name).get_public_url(file["name"])
                    print(f"Fallback to public URL for list: {file_url}")
            except Exception as sign_e:
                print(f"Error creating signed URL for list: {str(sign_e)}")
                # Fallback to public URL
                file_url = supabase_storage.supabase.storage.from_(supabase_storage.bucket_name).get_public_url(file["name"])
                print(f"Fallback to public URL for list: {file_url}")
                
            # Remove any query parameters from public URLs (but keep them for signed URLs)
            if '?' in file_url and 'token=' not in file_url:
                file_url = file_url.split('?')[0]
            
            images.append({
                "filename": file["name"],
                "url": file_url,
                "created_at": file.get("created_at", ""),
                "updated_at": file.get("updated_at", ""),
                "size": file.get("metadata", {}).get("size", 0)
            })
        
        return {
            "success": True,
            "count": len(images),
            "data": images
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error listing images: {str(e)}"
        }

@router.get("/{filename}")
async def get_image(filename: str) -> Any:
    """
    Get a specific image by filename.
    """
    try:
        # Check if file exists
        files = supabase_storage.supabase.storage.from_(supabase_storage.bucket_name).list()
        file_exists = any(file["name"] == filename for file in files)
        
        if not file_exists:
            return {
                "success": False,
                "message": f"Image '{filename}' not found"
            }
        
        # Try to create a signed URL with a long expiration time
        try:
            # Create a signed URL that expires in 10 years (effectively permanent)
            signed_url_data = supabase_storage.supabase.storage.from_(supabase_storage.bucket_name).create_signed_url(
                path=filename,
                expires_in=315360000  # 10 years in seconds
            )
            
            if signed_url_data and 'signedURL' in signed_url_data:
                file_url = signed_url_data['signedURL']
                print(f"Generated signed URL for get: {file_url}")
            else:
                # Fallback to public URL
                file_url = supabase_storage.supabase.storage.from_(supabase_storage.bucket_name).get_public_url(filename)
                print(f"Fallback to public URL for get: {file_url}")
        except Exception as sign_e:
            print(f"Error creating signed URL for get: {str(sign_e)}")
            # Fallback to public URL
            file_url = supabase_storage.supabase.storage.from_(supabase_storage.bucket_name).get_public_url(filename)
            print(f"Fallback to public URL for get: {file_url}")
            
        # Remove any query parameters from public URLs (but keep them for signed URLs)
        if '?' in file_url and 'token=' not in file_url:
            file_url = file_url.split('?')[0]
        
        return {
            "success": True,
            "filename": filename,
            "url": file_url
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error getting image: {str(e)}"
        }

@router.delete("/{filename}")
async def delete_image(filename: str) -> Any:
    """
    Delete an image by filename.
    """
    try:
        # Check if file exists
        files = supabase_storage.supabase.storage.from_(supabase_storage.bucket_name).list()
        file_exists = any(file["name"] == filename for file in files)
        
        if not file_exists:
            return {
                "success": False,
                "message": f"Image '{filename}' not found"
            }
        
        # Delete from Supabase
        supabase_storage.supabase.storage.from_(supabase_storage.bucket_name).remove([filename])
        
        return {
            "success": True,
            "message": f"Image '{filename}' deleted successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error deleting image: {str(e)}"
        }
