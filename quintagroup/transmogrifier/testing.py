from Testing.ZopeTestCase import installPackage
from Products.Five import zcml
from Products.Five import fiveconfigure
from collective.testcaselayer.ptc import BasePTCLayer, ptc_layer


class TransmogrifierLayer(BasePTCLayer):
    """ layer for integration tests """

    def afterSetUp(self):
        fiveconfigure.debug_mode = True
        from quintagroup import transmogrifier
        zcml.load_config('testing.zcml', transmogrifier)
        fiveconfigure.debug_mode = False
        installPackage('quintagroup.transmogrifier', quiet=True)
        self.addProfile('quintagroup.transmogrifier:default')


transmogrifier = TransmogrifierLayer(bases=[ptc_layer])
