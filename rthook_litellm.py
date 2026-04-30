"""
PyInstaller runtime hook for litellm / tiktoken.
Fixes two issues in frozen (PyInstaller) environment:
1. Sets TIKTOKEN_CACHE_DIR so tiktoken can find bundled tokenizer data.
2. Patches tiktoken's plugin discovery (pkgutil.iter_modules) which breaks
   in PyInstaller, by manually injecting ENCODING_CONSTRUCTORS.
"""
import os
import sys


def _patch_tiktoken():
    """Patch tiktoken registry so encoding discovery works without pkgutil."""
    try:
        import tiktoken_ext.openai_public as op
        from tiktoken import registry

        # If constructors are already populated, nothing to do
        if registry.ENCODING_CONSTRUCTORS is not None:
            return

        # Manually inject the constructors, bypassing _find_constructors()
        # which relies on pkgutil.iter_modules(tiktoken_ext.__path__)
        with registry._lock:
            if registry.ENCODING_CONSTRUCTORS is None:
                registry.ENCODING_CONSTRUCTORS = op.ENCODING_CONSTRUCTORS
    except Exception as e:
        # Don't crash the app if patching fails; litellm will show a clearer error
        print(f"[rthook_litellm] tiktoken patch failed: {e}")


# ── 禁用 litellm 远程拉取 model cost map（避免超时警告） ──
os.environ.setdefault('LITELLM_LOCAL_MODEL_COST_MAP', 'True')

if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS

    # ── Fix 1: TIKTOKEN_CACHE_DIR ──
    tokenizers_dir = os.path.join(base_dir, 'litellm', 'litellm_core_utils', 'tokenizers')
    if os.path.isdir(tokenizers_dir):
        if not os.getenv('CUSTOM_TIKTOKEN_CACHE_DIR'):
            os.environ['TIKTOKEN_CACHE_DIR'] = tokenizers_dir

    # ── Fix 2: Patch tiktoken plugin discovery ──
    _patch_tiktoken()
