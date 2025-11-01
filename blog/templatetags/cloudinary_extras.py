# /* ============================================================
#    *** BLOG: Template Tags (Cloudinary Extras) ***
#    ============================================================ */
"""Custom template tags and filters for Cloudinary integration."""

# /* ============================================================
#    *** BLOG: Template Tags: Imports ***
#    ============================================================ */
from __future__ import annotations

from django import template


# /* ============================================================
#    *** BLOG: Template Tags: Filters ***
#    ============================================================ */
register = template.Library()


@register.filter(name="cloudinary_variant")
def cloudinary_variant(original_url: str | None, transformation: str | None) -> str | None:
    """
    Insert a Cloudinary transformation right after 'upload/' in the URL.

    Example:
        {{ image.url|cloudinary_variant:
           "f_auto,q_auto,c_fill,g_auto:subject,ar_16:9,w_1200" }}
    """
    if not original_url or "upload/" not in original_url:
        return original_url
    if not transformation:
        return original_url
    part = transformation.strip()
    return original_url.replace("upload/", f"upload/{part}/", 1)
