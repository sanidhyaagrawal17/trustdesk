import os
import sys
from unittest.mock import MagicMock

# Disable Chroma telemetry by default
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"

# Provide fallback for grpc cygrpc if OS policy restricts C-extension DLL loading
if "grpc" not in sys.modules:
    try:
        import grpc
    except Exception:
        stub = MagicMock()
        stub.__version__ = "1.60.0"
        sys.modules["grpc"] = stub
        sys.modules["grpc._compression"] = stub
        sys.modules["grpc._cython"] = stub
        sys.modules["grpc._cython.cygrpc"] = stub
