
def id_to_slug(id):
    return max(0, int(id) + 821)


def slug_to_id(slug):
    return max(0, int(slug) - 821)
