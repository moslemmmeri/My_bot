# src/admin_panel/modules/logs_viewer/services/log_reader.py
import os
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from my_bot.core.exceptions import DatabaseError, NotFoundError, ValidationError
from my_bot.core.logger import get_logger
from my_bot.core.config import Config

logger = get_logger(__name__)


class LogReaderService:
    """Service for reading and managing log files."""

    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config.from_env()
        self.log_dir = Path(self.config.log_file_path).parent
        self.default_log_file = Path(self.config.log_file_path).name
        self.log_dir.mkdir(parents=True, exist_ok=True)

    async def list_log_files(self) -> List[Dict[str, Any]]:
        """List all log files in the log directory."""
        try:
            # Get all .log files
            log_files = []
            for file_path in self.log_dir.glob("*.log"):
                stat = file_path.stat()
                log_files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            # Sort by modification time descending
            log_files.sort(key=lambda x: x["modified"], reverse=True)
            return log_files
        except Exception as e:
            logger.error(f"Error listing log files: {e}", exc_info=True)
            raise DatabaseError("Failed to list log files.") from e

    async def read_log_file(
        self,
        filename: str,
        page: int = 1,
        page_size: int = 50,
        reverse: bool = True,
    ) -> Dict[str, Any]:
        """
        Read a log file with pagination.
        Returns dict with lines, total_lines, page, total_pages.
        """
        file_path = self.log_dir / filename
        if not file_path.exists():
            raise NotFoundError(f"Log file {filename} not found.")

        try:
            # Read file lines
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            total_lines = len(lines)
            if reverse:
                lines = list(reversed(lines))

            # Calculate pagination
            total_pages = (total_lines + page_size - 1) // page_size if total_lines > 0 else 1
            if page < 1:
                page = 1
            if page > total_pages:
                page = total_pages

            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_lines = lines[start_idx:end_idx]

            # Trim trailing newlines for display
            page_lines = [line.rstrip("\n") for line in page_lines]

            return {
                "lines": page_lines,
                "total_lines": total_lines,
                "page": page,
                "total_pages": total_pages,
                "filename": filename,
                "reverse": reverse,
            }
        except Exception as e:
            logger.error(f"Error reading log file {filename}: {e}", exc_info=True)
            raise DatabaseError(f"Failed to read log file {filename}.") from e

    async def search_log_file(
        self,
        filename: str,
        search_term: str,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Search for a term in a log file (case-insensitive).
        Returns paginated matching lines.
        """
        file_path = self.log_dir / filename
        if not file_path.exists():
            raise NotFoundError(f"Log file {filename} not found.")

        if not search_term.strip():
            raise ValidationError("Search term cannot be empty.")

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            # Find matching lines (keep original order)
            matches = []
            for line in lines:
                if search_term.lower() in line.lower():
                    matches.append(line.rstrip("\n"))

            total_matches = len(matches)
            total_pages = (total_matches + page_size - 1) // page_size if total_matches > 0 else 1
            if page < 1:
                page = 1
            if page > total_pages:
                page = total_pages

            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_lines = matches[start_idx:end_idx]

            return {
                "lines": page_lines,
                "total_lines": total_matches,
                "page": page,
                "total_pages": total_pages,
                "filename": filename,
                "search_term": search_term,
            }
        except Exception as e:
            logger.error(f"Error searching log file {filename}: {e}", exc_info=True)
            raise DatabaseError(f"Failed to search log file {filename}.") from e

    async def get_log_file_info(self, filename: str) -> Dict[str, Any]:
        """Get metadata about a log file."""
        file_path = self.log_dir / filename
        if not file_path.exists():
            raise NotFoundError(f"Log file {filename} not found.")

        try:
            stat = file_path.stat()
            # Count lines (optional, could be expensive for large files)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                line_count = sum(1 for _ in f)
            return {
                "name": filename,
                "path": str(file_path),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "line_count": line_count,
            }
        except Exception as e:
            logger.error(f"Error getting info for log file {filename}: {e}", exc_info=True)
            raise DatabaseError(f"Failed to get log file info.") from e

    async def clear_log_file(self, filename: str) -> bool:
        """Clear the contents of a log file (truncate)."""
        file_path = self.log_dir / filename
        if not file_path.exists():
            raise NotFoundError(f"Log file {filename} not found.")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.truncate(0)
            logger.info(f"Log file {filename} cleared.")
            return True
        except Exception as e:
            logger.error(f"Error clearing log file {filename}: {e}", exc_info=True)
            raise DatabaseError(f"Failed to clear log file.") from e

    async def get_log_levels(self, filename: str) -> Dict[str, int]:
        """
        Get counts of log levels (ERROR, WARNING, INFO, DEBUG) in a log file.
        """
        file_path = self.log_dir / filename
        if not file_path.exists():
            raise NotFoundError(f"Log file {filename} not found.")

        try:
            levels = {"ERROR": 0, "WARNING": 0, "INFO": 0, "DEBUG": 0}
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line_upper = line.upper()
                    for level in levels.keys():
                        if level in line_upper:
                            levels[level] += 1
                            break  # count only the first level in the line
            return levels
        except Exception as e:
            logger.error(f"Error counting log levels in {filename}: {e}", exc_info=True)
            raise DatabaseError("Failed to count log levels.") from e