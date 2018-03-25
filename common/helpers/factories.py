__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory


class FormFactory(factory.Factory):
    class Meta:
        strategy = factory.BUILD_STRATEGY

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        return model_class(kwargs)
