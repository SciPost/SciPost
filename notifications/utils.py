__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


def slug2id(slug):
    return int(slug) - 9631


def id2slug(id):
    return id + 9631
