import os
import tempfile

# Isolate every test run from the demo data before any dossiergraph module is imported.
os.environ["DG_DATA"] = tempfile.mkdtemp(prefix="dg-test-")
