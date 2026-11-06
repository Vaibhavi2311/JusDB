
from backend.app.graph_store import (
    verify_connection,
    close_connection
)

try:
    verify_connection()
finally:
    close_connection()
