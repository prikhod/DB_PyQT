class BadMessageError(Exception):
    def __str__(self):
        return 'incorrect message.'
