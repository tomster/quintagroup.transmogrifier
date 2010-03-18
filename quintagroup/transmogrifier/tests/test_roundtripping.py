from unittest import defaultTestLoader
from quintagroup.transmogrifier.tests.base import TransmogrifierTestCase


class SetupTests(TransmogrifierTestCase):

    def testTransmogrifierInstalled(self):
        portal_setup = self.portal.portal_setup
        self.failUnless(u'quintagroup.transmogrifier:default' in
            [info['id'] for info in  portal_setup.listProfileInfo()]
        )


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)

