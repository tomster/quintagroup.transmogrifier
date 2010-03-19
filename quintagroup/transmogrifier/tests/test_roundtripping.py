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
        report = {
            'diff_files' : comparison.diff_files,
            'funny_files' : comparison.funny_files
        }
        for sd in comparison.subdirs.itervalues():
            report.update(self.recursive_comparison(sd))
        return report


    def testTripWireExport(self):
        """ A basic sanity check. We create demo data, normalize it, export it
            and then recursively compare its file structure with a previous 
            snapshot of that export (which has been added to the test fixture.
            
            This enables us to detect changes in the marshalling. If this test
            begins to fail, we should simply commit the new structure to the
            fixture (after anyalyzing the differences) to make the test pass
            again.
        """        
        # normalize uid, creation and modifcation dates to enable meaningful
        # diffs
        self.loginAsPortalOwner()
        for brain in self.portal.portal_catalog():
            obj = brain.getObject()
            obj.setModificationDate('2010-01-01T14:00:00Z')
            obj.setCreationDate('2010-01-01T14:00:00Z')
            obj._at_uid = brain.getPath()
        
        # monkeypatch the CMF marshaller to exclude the workflow history
        # as that information is difficult to normalize
        from quintagroup.transmogrifier.namespaces.cmfns import CMF
        CMF.attributes = (CMF.attributes[0], CMF.attributes[2])

        # perform the actual export
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
        snapshot_structure_path = '%s/reference_export/' % self.data_path
        comparison = dircmp(snapshot_structure_path, exported_structure_path)

        # for the test we check that there are no files that differ
        # and that all files were comparable (funny_files)
        report = self.recursive_comparison(comparison)
        self.assertEqual(report['diff_files'], [])
        self.assertEqual(report['funny_files'], [])

def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)

