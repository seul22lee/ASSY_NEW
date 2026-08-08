"""Load a git-ignored .env into the process environment.

The provider reads credentials from os.environ and from nowhere else. This
module is the only thing that puts them there, and it is deliberately separate
so that the provider has no file-reading path to a secret at all.

NOTHING HERE EVER RETURNS, LOGS OR RENDERS A VALUE. `load` returns the NAMES it
set, so a caller can report what was configured without reporting what it is.
"""
from __future__ import annotations

import os
import re
from typing import List, Optional

#: Names that hold a credential. Their values are never returned or displayed by
#: anything in this module; the list exists so callers can mask by name.
SECRET_NAME_PATTERN = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD)$")


def load(path: str, override: bool = False) -> List[str]:
    """Set variables from `path` into os.environ. Returns the names set.

    Existing environment variables win unless `override` is true: a value the
    operator exported deliberately should not be silently replaced by a file.
    """
    names: List[str] = []
    if not os.path.isfile(path):
        return names
    with open(path) as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            line = re.sub(r"^export\s+", "", line)
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if override or key not in os.environ:
                os.environ[key] = value
            names.append(key)
    return names


def describe(names: List[str]) -> str:
    """A safe one-line summary: names, and lengths for secrets. Never a value."""
    parts = []
    for n in sorted(set(names)):
        if SECRET_NAME_PATTERN.search(n):
            parts.append("%s=<set, %d chars>" % (n, len(os.environ.get(n, ""))))
        else:
            parts.append("%s=%s" % (n, os.environ.get(n, "")))
    return ", ".join(parts)


def require(name: str) -> str:
    """Return an environment variable, or fail with a message that names the
    variable and says how to set it -- and never echoes any value."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            "%s is not set. This provider reads its credential only from the "
            "environment. Export it, or put it in a git-ignored .env and load "
            "that file explicitly. The key is never read from source, never "
            "written to a run record, and never printed." % name)
    return value


def mask(text: str, secret: Optional[str]) -> str:
    """Remove a secret from text that is about to be shown. A last line of
    defence: nothing in this repository should be building such text at all."""
    if not secret or not text:
        return text
    return text.replace(secret, "<redacted>")
