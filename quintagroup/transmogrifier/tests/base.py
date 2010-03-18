import os
import quintagroup
from Products.Five.testbrowser import Browser
from Products.PloneTestCase import ptc
from quintagroup.transmogrifier import testing


ptc.setupPloneSite()


class TransmogrifierTestCase(ptc.PloneTestCase):
    """ base class for integration tests """

    layer = testing.transmogrifier

    data_path = os.path.join(quintagroup.transmogrifier.tests.__path__[0],
        "data")


class TransmogrifierFunctionalTestCase(ptc.FunctionalTestCase):
    """ base class for functional tests """

    layer = testing.transmogrifier

    def getCredentials(self):
        return '%s:%s' % (ptc.default_user, ptc.default_password)

    def getBrowser(self, loggedIn=True):
        """ instantiate and return a testbrowser for convenience """
        browser = Browser()
        if loggedIn:
            auth = 'Basic %s' % self.getCredentials()
            browser.addHeader('Authorization', auth)
        return browser
