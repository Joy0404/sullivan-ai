"""Public build identity, captured on import to detect an outdated running server."""
from uuid import uuid4

BUILD='sullivan-roles-20261102-r2'
INSTANCE=uuid4().hex[:8]
