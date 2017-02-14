class ArxivCallable(object):
    '''Models that contain a Arxiv identification should contain these
    methods to be compatible with the ArxivCaller().
    '''
    @classmethod
    def same_version_exists(self, identifier):
        '''Check if the given identifier already is present in the database.'''
        raise NotImplementedError
