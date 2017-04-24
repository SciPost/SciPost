import random
import string


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


def random_digits(n):
    return "".join(random.choice(string.digits) for _ in range(n))


def filter_keys(dictionary, keys_to_keep):
    # Field is empty if not on model.
    return {key: dictionary.get(key, "") for key in keys_to_keep}
