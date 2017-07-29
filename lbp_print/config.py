"""Settings module making general variables globally available.

To change any settings, simply overwrite then after import."""

import os
import tempfile

cache_dir = None
temp_dir = tempfile.TemporaryDirectory()
module_dir = os.path.dirname(__file__)