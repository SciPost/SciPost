__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import hashlib
import random
import string


def model_form_data(model, form_class, form_kwargs={}):
    """
    Returns a dict that can be used to instantiate a form object.
    It fills in the model's data, but filters out fields that are not on the form.
    Example:

    class Car(models.Model):
        brand = CharField(max_length = 50)
        fuel_tank_size = FloatField()
        # more fields

    class CreateCarForm(forms.ModelForm):
        fields = ['brand']

    my_car = Car(brand='Nissan', fuel_tank_size=60)

    model_form_data(my_car, CreateCarForm)
    # returns {'brand': 'Nissan'}

    Note that the returned dict does not have a field 'fuel_tank_size', because it is not
    on the form.
    """

    model_data = model.__dict__
    form_fields = list(form_class(**form_kwargs).fields.keys())
    return filter_keys(model_data, form_fields)


def random_arxiv_identifier_with_version_number(version_nr="0"):
    return random_arxiv_identifier_without_version_number() + "v" + str(version_nr)


def random_arxiv_identifier_without_version_number():
    return random_digits(4) + "." + random_digits(5)


def random_scipost_journal():
    return random.choice(
        (
            "SciPostPhys",
            "SciPostPhysLectNotes",
            "SciPostPhysProc",
            "SciPostMath",
            "SciPostChem",
        )
    )


def random_external_journal_abbrev():
    return random.choice(
        (
            "Ann. Phys.",
            "Phys. Rev. A",
            "Phys. Rev. B",
            "Phys. Rev. C",
            "Phys. Rev. Lett.",
            "Europhys. Lett.",
            "J. Math. Anal. Appl.",
            "Nat. Phys." "J. Phys. A",
            "J. Stat. Phys.",
            "J. Stat. Mech.",
            "J. Math. Phys.",
            "Lett. Math. Phys.",
            "Sov. Phys. JETP",
            "Sov. Phys. JETP",
            "Nucl. Phys. B",
            "Adv. Phys.",
        )
    )


def random_pub_number():
    return "%i.%i.%s" % (random.randint(1, 9), random.randint(1, 9), random_digits(3))


def random_scipost_doi():
    return "10.21468/%s.%s" % (random_scipost_journal(), random_pub_number())


def random_scipost_report_doi_label():
    return "SciPost.Report.%s" % random_digits(4)


def random_external_doi():
    """
    Return a fake/random doi as if all journal abbrev and pub_number are separated by `.`, which
    can be helpfull for testing purposes.
    """
    journal = random.choice(
        (
            "PhysRevA",
            "PhysRevB",
            "PhysRevC",
            "PhysRevLett",
            "nature" "S0550-3213(01)",
            "1742-5468",
            "0550-3213(96)",
        )
    )
    return "10.%s/%s.%s" % (random_digits(5), journal, random_pub_number())


def random_digits(n):
    return "".join(random.choice(string.digits) for _ in range(n))


def generate_orcid():
    return "{}-{}-{}-{}".format(
        random_digits(4),
        random_digits(4),
        random_digits(4),
        random_digits(4),
    )


def filter_keys(dictionary, keys_to_keep):
    # Field is empty if not on model.
    return {key: dictionary.get(key, "") for key in keys_to_keep}


def get_new_secrets_key(salt="", salt2=""):
    key = salt or generate_orcid()
    for i in range(5):
        key += random.choice(string.ascii_letters)
    key = key.encode("utf8")
    return hashlib.sha1(key + salt2.encode("utf8")).hexdigest()
