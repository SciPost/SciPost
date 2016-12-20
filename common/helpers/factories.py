import factory


class FormFactory(factory.Factory):
    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        return model_class(kwargs)
