"""Validator for discovered files."""

from datetime import datetime
from typing import Dict, List, Optional

from ..domain.entities import DiscoveredFile
from ..domain.errors import ValidationError
from ..domain.policies import AcceptancePolicy
from ..domain.value_objects import BytesSizeKB, MimeType
from ..interfaces.http_port import HttpPort
from ..interfaces.logger_port import LoggerPort


class Validator:
    """Validator for discovered files."""

    def __init__(self, http_port: HttpPort, logger: LoggerPort):
        """Initialize validator."""
        self.http = http_port
        self.logger = logger

    def validate(
        self, candidates: List[DiscoveredFile], expect_config: Dict
    ) -> List[DiscoveredFile]:
        """Validate candidates by HEAD/GET and expectations.
        
        Returns:
            List of valid candidates with metadata populated
        """
        valid_candidates = []
        
        mime_any = expect_config.get("mime_any", [])
        min_size_kb = expect_config.get("min_size_kb", 0)
        
        for candidate in candidates:
            try:
                # Try HEAD first
                headers, error = self.http.head(candidate.url.value)
                
                if error:
                    # HEAD failed, try GET
                    self.logger.debug(
                        "HEAD failed, trying GET",
                        url=candidate.url.value,
                        error=error,
                    )
                    content, headers, error_get = self.http.get(candidate.url.value)
                    
                    if error_get or not headers:
                        self.logger.debug(
                            "GET also failed",
                            url=candidate.url.value,
                            error=error_get,
                        )
                        continue
                    
                    # GET succeeded
                    candidate.notes = "head_failed_get_ok"
                    if content:
                        candidate.size_kb = BytesSizeKB.from_bytes(len(content))
                else:
                    # HEAD succeeded
                    if headers:
                        content_length = headers.get("content-length")
                        if content_length:
                            try:
                                candidate.size_kb = BytesSizeKB.from_bytes(int(content_length))
                            except (ValueError, TypeError):
                                pass
                
                # Extract metadata from headers
                if headers:
                    content_type = headers.get("content-type", "")
                    if content_type:
                        # Remove charset if present
                        content_type = content_type.split(";")[0].strip()
                        try:
                            candidate.mime = MimeType(value=content_type)
                        except Exception:
                            pass
                    
                    last_modified = headers.get("last-modified")
                    if last_modified:
                        try:
                            candidate.last_modified = datetime.strptime(
                                last_modified, "%a, %d %b %Y %H:%M:%S %Z"
                            )
                        except (ValueError, TypeError):
                            pass
                
                # Check acceptance policies
                mime_ok = AcceptancePolicy.check_mime(
                    mime_any, candidate.mime.value if candidate.mime else None
                )
                
                size_ok = AcceptancePolicy.check_min_size(
                    min_size_kb, candidate.size_kb.value if candidate.size_kb else None
                )
                
                if not mime_ok:
                    self.logger.debug(
                        "MIME mismatch",
                        url=candidate.url.value,
                        expected=mime_any,
                        got=candidate.mime.value if candidate.mime else None,
                    )
                    continue
                
                if not size_ok:
                    self.logger.debug(
                        "Size too small",
                        url=candidate.url.value,
                        min_kb=min_size_kb,
                        got_kb=candidate.size_kb.value if candidate.size_kb else None,
                    )
                    continue
                
                # Valid candidate
                valid_candidates.append(candidate)
                self.logger.debug(
                    "Candidate validated",
                    url=candidate.url.value,
                    mime=candidate.mime.value if candidate.mime else None,
                    size_kb=candidate.size_kb.value if candidate.size_kb else None,
                )
                
            except Exception as e:
                self.logger.error(
                    "Validation error",
                    url=candidate.url.value,
                    error=str(e),
                )
                continue
        
        return valid_candidates

