__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


IS_INSTANCE_OF = 'is_instance_of'
IS_SPECIALIZATION_OF = 'is_specialization_of'
IS_REFINEMENT_OF = 'is_refinement_of'
IS_USED_IN = 'is_used_in'
IS_EXAMPLE_OF = 'is_example_of'

TOPIC_RELATIONS_ASYM = (
    (IS_INSTANCE_OF, 'is an instance of'),
    (IS_SPECIALIZATION_OF, 'is a specialization of'),
    (IS_REFINEMENT_OF, 'is a refinement of'),
    (IS_USED_IN, 'is used in'),
    (IS_EXAMPLE_OF, 'is an example of'),
)


ARE_RELATED = 'are_related'
ARE_SYNONYMS = 'are_synonyms'

TOPIC_RELATIONS_SYM = (
    (ARE_RELATED, 'are related'),
    (ARE_SYNONYMS, 'are synonyms'),
)
