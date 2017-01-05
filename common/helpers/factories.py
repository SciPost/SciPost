import factory


class FormFactory(factory.Factory):
    class Meta:
        strategy = factory.BUILD_STRATEGY

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        return model_class(kwargs)
