# ============================================================
#    *** PAGES: Package exports (constants + helpers) ***
# ============================================================

"""Expose homepage constants and helpers for reuse in views/tests."""

# Homepage constants
HOME_FEATURED_POST_LIMIT = 6
HOME_FEATURED_GALLERY_LIMIT = 10
HOME_OTHER_POSTS_PER_PAGE = 6


def home_posts_queryset(*, featured: bool):
    """Return queryset of APPROVED posts filtered by 'featured' flag.

    Lazy import avoids triggering Django app loading during static analysis.
    """
    from blog.models import BlogPost  # pylint: disable=import-outside-toplevel

    return (
        BlogPost.objects.filter(
            featured=featured,
            status=BlogPost.STATUS_APPROVED,
        )
        .select_related("author")
        .order_by("-published_at", "-updated_at")
    )


__all__ = [
    "HOME_FEATURED_POST_LIMIT",
    "HOME_FEATURED_GALLERY_LIMIT",
    "HOME_OTHER_POSTS_PER_PAGE",
    "home_posts_queryset",
]
