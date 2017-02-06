class ArxivCallable(object):
    '''Models that contain a Arxiv identification should contain these
    methods to be compatible with the ArxivCaller().
    '''
    @classmethod
    def same_version_exists(self, identifier):
        '''Check if the given identifier already is present in the database.'''
        raise NotImplementedError

    @classmethod
    def different_versions(self, identifier):
        '''Return all different versions present in the database related to the identifier.'''
        raise NotImplementedError
