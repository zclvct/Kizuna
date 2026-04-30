"""
PyInstaller runtime hook for litellm.
Sets TIKTOKEN_CACHE_DIR to the bundled tokenizers directory before litellm loads.
In PyInstaller onedir mode, data files are placed relative to sys._MEIPASS.
"""
import os
import sys

# In PyInstaller, sys._MEIPASS points to the temp extraction directory
# For onedir mode, data files are in the same directory as the executable
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
    tokenizers_dir = os.path.join(base_dir, 'litellm', 'litellm_core_utils', 'tokenizers')
    if os.path.isdir(tokenizers_dir):
        # Only set if not explicitly overridden by user
        if not os.getenv('CUSTOM_TIKTOKEN_CACHE_DIR'):
            os.environ['TIKTOKEN_CACHE_DIR'] = tokenizers_dir
