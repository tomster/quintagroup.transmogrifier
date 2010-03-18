# -*- coding: utf-8 -*-
import tempfile
from filecmp import dircmp
from tarfile import TarFile
from unittest import defaultTestLoader
from quintagroup.transmogrifier.tests.base import TransmogrifierTestCase


class SetupTests(TransmogrifierTestCase):

    def testTransmogrifierInstalled(self):
        # a simple sanity check whether the profile we're testing
        # is actually installed in our fixture
        portal_setup = self.portal.portal_setup
        self.failUnless(u'quintagroup.transmogrifier:default' in
            [info['id'] for info in  portal_setup.listProfileInfo()]
        )

class RoundtrippingTests(TransmogrifierTestCase):
    """ These tests export content, re-import it and make sure
        that we get what we expect.
    """

    def recursive_comparison(self, comparison): 
        report = {}
        report['diff_files'] = comparison.diff_files
        report['funny_files'] = comparison.funny_files
        for sd in comparison.subdirs.itervalues():
            report.update(self.recursive_comparison(sd))
        return report


    def testTripWireExport(self):
        self.loginAsPortalOwner()
        self.portal.news.invokeFactory('News Item', id='hold-the-press', title=u"Høld the Press!")
        self.portal.events.invokeFactory('Event', id='party', title=u"Süper Pärty")
        setup = self.portal.portal_setup
        result = setup._doRunExportSteps(['content_quinta'])
        tempfolder = tempfile.mkdtemp()
        tgz_filename = "%s/%s" % (tempfolder, result['filename'])
        tgz = open(tgz_filename, 'w')
        tgz.write(result['tarball'])
        tgz.close()
        exported = TarFile.open(tgz_filename, 'r:gz')
        exported_structure_path = '%s/exported/' % tempfolder
        exported.extractall(exported_structure_path)
        reference_structure_path = '%s/reference_export/' % self.data_path

        comparison = dircmp(reference_structure_path,
            exported_structure_path)

        report = self.recursive_comparison(comparison)
        self.assertEqual(report['diff_files'], [])
        self.assertEqual(report['funny_files'], [])


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)

