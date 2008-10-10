from zope.interface import Interface

class IExportDataCorrector(Interface):
    """ Inteface for components that do some correction on exported data.
    """

    def __call__(data):
        """ Correct data given in 'data' argument and return it.
        """
