"""Semantic Versioning (SemVer 2.0.0) Specification & Core Version Registry.

Single source of truth for NewsAlerts application versioning.
Complies strictly with Semantic Versioning 2.0.0: https://semver.org/
Format: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional, Tuple

# Current application version (Single Source of Truth)
__version__ = "2.4.4"
VERSION_INFO = (2, 4, 4)

# Official SemVer 2.0.0 regex pattern
SEMVER_REGEX = re.compile(
    r"^(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


@dataclass(frozen=True)
class SemVer:
    """Represents a validated Semantic Version."""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    @classmethod
    def parse(cls, version_str: str) -> SemVer:
        """Parse and validate a Semantic Version string.
        
        Strips optional leading 'v' for user convenience if present.
        """
        raw = version_str.strip()
        if raw.startswith("v") or raw.startswith("V"):
            raw = raw[1:]

        match = SEMVER_REGEX.match(raw)
        if not match:
            raise ValueError(
                f"Invalid Semantic Version string: '{version_str}'. "
                "Must match SemVer 2.0.0 format: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]"
            )

        groups = match.groupdict()
        return cls(
            major=int(groups["major"]),
            minor=int(groups["minor"]),
            patch=int(groups["patch"]),
            prerelease=groups.get("prerelease"),
            build=groups.get("buildmetadata"),
        )

    @classmethod
    def is_valid(cls, version_str: str) -> bool:
        """Check if a string is a valid Semantic Version."""
        try:
            cls.parse(version_str)
            return True
        except ValueError:
            return False

    def bump_major(self) -> SemVer:
        """Increment MAJOR version, resetting MINOR and PATCH to 0."""
        return SemVer(major=self.major + 1, minor=0, patch=0)

    def bump_minor(self) -> SemVer:
        """Increment MINOR version, resetting PATCH to 0."""
        return SemVer(major=self.major, minor=self.minor + 1, patch=0)

    def bump_patch(self) -> SemVer:
        """Increment PATCH version."""
        return SemVer(major=self.major, minor=self.minor, patch=self.patch + 1)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "version": str(self),
            "tag": f"v{self}",
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "prerelease": self.prerelease,
            "build": self.build,
            "is_prerelease": self.prerelease is not None,
        }

    def __str__(self) -> str:
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            s += f"-{self.prerelease}"
        if self.build:
            s += f"+{self.build}"
        return s

    def __repr__(self) -> str:
        return f"SemVer({self})"

    def _sort_key(self) -> Tuple[int, int, int, int, Any]:
        # Pre-releases have lower precedence than normal releases
        # 1 if no pre-release (final), 0 if pre-release exists
        is_final = 1 if self.prerelease is None else 0
        return (self.major, self.minor, self.patch, is_final, self.prerelease or "")

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self._sort_key() < other._sort_key()

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self._sort_key() <= other._sort_key()

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self._sort_key() > other._sort_key()

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self._sort_key() >= other._sort_key()


def get_version() -> str:
    """Return the current SemVer version string (e.g. '2.4.0')."""
    return __version__


def get_version_tag() -> str:
    """Return the git tag representation (e.g. 'v2.4.0')."""
    return f"v{__version__}"


def get_version_info() -> dict[str, Any]:
    """Return structured Semantic Version metadata for UI and diagnostics."""
    parsed = SemVer.parse(__version__)
    return parsed.to_dict()


def validate_semver(version_str: str) -> bool:
    """Check whether a version string complies with SemVer 2.0.0."""
    return SemVer.is_valid(version_str)
