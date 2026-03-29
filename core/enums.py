from __future__ import annotations

from enum import StrEnum


class Severity(StrEnum):
    INFO = "info"
    WATCH = "watch"
    IMPORTANT = "important"
    HIGH = "high"


class FindingCategory(StrEnum):
    STRUCTURAL = "structural"
    DUPLICATION = "duplication"
    GIT = "git"
    HYGIENE = "hygiene"


class ScanState(StrEnum):
    IDLE = "idle"
    SCANNING = "scanning"
    SCANNED = "scanned"
    STALE = "stale"
    ERROR = "error"


class GitStatusKind(StrEnum):
    CLEAN = "clean"
    MODIFIED = "modified"
    DELETED = "deleted"
    UNTRACKED = "untracked"


class IgnoreType(StrEnum):
    BUILD = "build"
    CACHE = "cache"
    LOGS = "logs"
    TEMP = "temp"
    GENERATED = "generated"
    LOCAL = "local"


class ViewName(StrEnum):
    OVERVIEW = "overview"
    HOTSPOTS = "hotspots"
    GIT = "git"
    IGNORE = "ignore"
    FILES = "files"
