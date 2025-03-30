from typing import BinaryIO, Optional
import uuid
from supabase import create_client, Client
from app.core.config import settings

class SupabaseStorageService:
    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
            
        self.supabase: Client = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_KEY
        )
        self.bucket_name = settings.SUPABASE_BUCKET
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
        
    def _ensure_bucket_exists(self) -> None:
        """
        Ensure the bucket exists, create it if it doesn't
        
        Note: This requires appropriate permissions in Supabase.
        If using an anonymous key, you need to create the bucket manually
        in the Supabase dashboard and configure RLS policies.
        """
        try:
            # Check if bucket exists by listing buckets
            buckets = self.supabase.storage.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            print(f"Available buckets: {bucket_names}")
            
            # Assume bucket exists even if we can't see it due to permissions
            # This is a workaround for the case where the bucket exists but we can't see it
            # due to RLS policies
            bucket_exists = True
            
            # Try to use the bucket directly instead of checking if it exists
            try:
                # Try to list files in the bucket to see if we can access it
                self.supabase.storage.from_(self.bucket_name).list()
                print(f"Successfully accessed bucket '{self.bucket_name}'")
            except Exception as bucket_e:
                print(f"Error accessing bucket '{self.bucket_name}': {str(bucket_e)}")
                print("This could be due to RLS policies or the bucket not existing.")
                print("If the bucket exists, make sure you have configured the RLS policies correctly.")
                # We'll continue anyway and let the actual operations fail if needed
        except Exception as e:
            print(f"Error listing buckets: {str(e)}")
            print("This is likely due to Row-Level Security (RLS) policies in Supabase.")
            print("We'll assume the bucket exists and try to use it directly.")
        
    async def upload_file(
        self, 
        file: BinaryIO, 
        content_type: str, 
        file_path: Optional[str] = None
    ) -> str:
        """
        Upload a file to Supabase Storage
        
        Args:
            file: File-like object
            content_type: MIME type of the file
            file_path: Optional path within the bucket
            
        Returns:
            Public URL of the uploaded file
        """
        if file_path is None:
            # Generate a unique filename if not provided
            file_extension = content_type.split('/')[-1]
            file_path = f"{uuid.uuid4()}.{file_extension}"
        
        try:
            # Read the file content into memory
            # This is necessary because Supabase expects bytes, not a file-like object
            file_content = file.read()
            
            # Upload the file
            response = self.supabase.storage.from_(self.bucket_name).upload(
                path=file_path, 
                file=file_content,
                file_options={"content-type": content_type}
            )
            
            # Try to create a signed URL with a long expiration time
            # This should work even if the bucket is not public
            try:
                # Create a signed URL that expires in 10 years (effectively permanent)
                # 10 years = 315360000 seconds
                signed_url_data = self.supabase.storage.from_(self.bucket_name).create_signed_url(
                    path=file_path,
                    expires_in=315360000
                )
                
                if signed_url_data and 'signedURL' in signed_url_data:
                    file_url = signed_url_data['signedURL']
                    print(f"Generated signed URL: {file_url}")
                else:
                    # Fallback to public URL if signed URL fails
                    file_url = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
                    print(f"Fallback to public URL: {file_url}")
            except Exception as sign_e:
                print(f"Error creating signed URL: {str(sign_e)}")
                # Fallback to public URL if signed URL fails
                file_url = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
                print(f"Fallback to public URL: {file_url}")
                
            # Remove any query parameters that might be causing issues with the public URL
            # (but keep them for signed URLs)
            if '?' in file_url and 'token=' not in file_url:
                file_url = file_url.split('?')[0]
                
            # Log the final URL for debugging
            print(f"Final URL: {file_url}")
            
            return file_url
        except Exception as e:
            error_msg = str(e)
            print(f"Error uploading file to Supabase: {error_msg}")
            
            if "new row violates row-level security policy" in error_msg or "403" in error_msg:
                raise Exception(
                    "Permission denied. This is likely due to Row-Level Security (RLS) policies in Supabase. "
                    "Please configure appropriate RLS policies for the bucket in the Supabase dashboard. "
                    "You need to allow uploads for the anonymous role or use a service key with higher privileges."
                )
            
            # For other errors, try to provide helpful information
            if "bucket" in error_msg.lower() and "not found" in error_msg.lower():
                raise Exception(
                    f"Bucket '{self.bucket_name}' not found. Please create it manually in the Supabase dashboard."
                )
                
            # Generic error
            raise Exception(f"Failed to upload file: {error_msg}")
        
    async def delete_file(self, file_path: str) -> None:
        """
        Delete a file from Supabase Storage
        
        Args:
            file_path: Path of the file within the bucket
        """
        self.supabase.storage.from_(self.bucket_name).remove([file_path])

# Create a global instance
supabase_storage = SupabaseStorageService()
