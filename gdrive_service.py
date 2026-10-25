import os
import time
import subprocess
import logging
from typing import List, Dict, Any, Optional, Generator

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class GDrivePhotoService:
    def __init__(self, remote_path: str = "gdriv:PhotosForRaspi"):
        self.remote_path = remote_path.rstrip("/")
        self.cached_files: List[str] = []
        self.last_fetch_time: float = 0.0
        self.cache_ttl: float = 600.0  # 10 minutes cache TTL

    def is_rclone_installed(self) -> bool:
        """Check if rclone binary is present in PATH."""
        try:
            res = subprocess.run(["which", "rclone"], capture_output=True, text=True)
            return res.returncode == 0
        except Exception:
            return False

    def get_photos_list(self) -> Dict[str, Any]:
        """Lists supported photo filenames from rclone remote path."""
        now = time.time()
        if self.cached_files and (now - self.last_fetch_time < self.cache_ttl):
            return {
                "available": True,
                "photos": self.cached_files,
                "count": len(self.cached_files),
                "cached": True
            }

        if not self.is_rclone_installed():
            logger.warning("rclone is not installed on this system.")
            return {
                "available": False,
                "photos": [],
                "count": 0,
                "error": "rclone is not installed"
            }

        try:
            # Run rclone lsf --files-only to list files in gdriv:PhotosForRaspi
            cmd = ["rclone", "lsf", "--files-only", self.remote_path]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if res.returncode != 0:
                err_msg = res.stderr.strip() or "rclone command failed"
                logger.warning(f"rclone lsf error: {err_msg}")
                return {
                    "available": False,
                    "photos": self.cached_files,  # Retain previous cache if available
                    "count": len(self.cached_files),
                    "error": err_msg
                }

            filenames = []
            for line in res.stdout.splitlines():
                filename = line.strip()
                if not filename:
                    continue
                ext = os.path.splitext(filename)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    filenames.append(filename)

            self.cached_files = filenames
            self.last_fetch_time = now

            return {
                "available": True,
                "photos": filenames,
                "count": len(filenames),
                "cached": False
            }
        except subprocess.TimeoutExpired:
            logger.warning("rclone lsf timed out")
            return {
                "available": False,
                "photos": self.cached_files,
                "count": len(self.cached_files),
                "error": "rclone lsf timed out"
            }
        except Exception as e:
            logger.warning(f"Failed to list photos: {e}")
            return {
                "available": False,
                "photos": self.cached_files,
                "count": len(self.cached_files),
                "error": str(e)
            }

    def stream_photo(self, filename: str) -> Optional[Generator[bytes, None, None]]:
        """Streams image bytes directly from rclone on-demand without local disk persistence."""
        # Sanitize filename to prevent directory traversal
        safe_filename = os.path.basename(filename)
        ext = os.path.splitext(safe_filename)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            logger.warning(f"Unauthorized file extension requested: {filename}")
            return None

        if not self.is_rclone_installed():
            return None

        full_remote_file = f"{self.remote_path}/{safe_filename}"
        try:
            # Stream image content on-demand via rclone cat
            proc = subprocess.Popen(
                ["rclone", "cat", full_remote_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            def generate():
                try:
                    while True:
                        chunk = proc.stdout.read(65536)
                        if not chunk:
                            break
                        yield chunk
                finally:
                    proc.stdout.close()
                    proc.wait()

            return generate()
        except Exception as e:
            logger.warning(f"Failed to stream photo {safe_filename}: {e}")
            return None

    def get_mime_type(self, filename: str) -> str:
        safe_filename = os.path.basename(filename)
        ext = os.path.splitext(safe_filename)[1].lower()
        if ext in (".jpg", ".jpeg"):
            return "image/jpeg"
        elif ext == ".png":
            return "image/png"
        elif ext == ".webp":
            return "image/webp"
        return "application/octet-stream"
