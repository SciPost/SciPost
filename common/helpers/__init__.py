import random
import string

from journals.constants import SCIPOST_JOURNALS_SUBMIT


def model_form_data(model, form_class, form_kwargs={}):
    '''
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
    '''

    model_data = model.__dict__
    form_fields = list(form_class(**form_kwargs).fields.keys())
    return filter_keys(model_data, form_fields)


def random_arxiv_identifier_with_version_number():
    return random_arxiv_identifier_without_version_number() + "v0"


def random_arxiv_identifier_without_version_number():
    return random_digits(4) + "." + random_digits(5)


def random_scipost_journal():
    return random.choice(SCIPOST_JOURNALS_SUBMIT)[0]


def random_external_journal():
    return random.choice((
        'PhysRevA.',
        'PhysRevB.',
        'PhysRevC.',
        'nature.'
        'S0550-3213(01)',
        '1742-5468/',
        '0550-3213(96)'
    ))


def random_pub_number():
    return '%i.%i.%s' % (random.randint(1, 9), random.randint(1, 9), random_digits(3))


def random_scipost_doi():
    return '10.21468/%s.%s' % (random_scipost_journal(), random_pub_number())


def random_external_doi():
    return '10.%s/%s%s' % (random_digits(5), random_external_journal(), random_pub_number())


def random_digits(n):
    return "".join(random.choice(string.digits) for _ in range(n))


def filter_keys(dictionary, keys_to_keep):
    # Field is empty if not on model.
    return {key: dictionary.get(key, "") for key in keys_to_keep}
