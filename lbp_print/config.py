"""Settings module making general variables globally available.

To change any settings, simply overwrite then after import."""

import logging
import os

cache_dir = os.path.join(os.path.expanduser("~"), ".lbp_cache")
module_dir = os.path.dirname(__file__)
log_level = logging.INFO
