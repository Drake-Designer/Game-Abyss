from django import template

register = template.Library()


@register.filter
def cloudinary_variant(original_url, transformation):
    """
    Insert a Cloudinary transformation right after 'upload/' in the URL.
    Example:
      {{ image.url|cloudinary_variant:"f_auto,q_auto,c_fill,g_auto:subject,ar_16:9,w_1200" }}
    """
    if not original_url or 'upload/' not in original_url:
        return original_url
    return original_url.replace('upload/', f"upload/{transformation.strip()}/", 1)
