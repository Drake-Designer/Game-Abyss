import logging

try:
    import cssutils
except ImportError:
    cssutils = None

if cssutils:
    cssutils.log.setLevel(logging.CRITICAL)
