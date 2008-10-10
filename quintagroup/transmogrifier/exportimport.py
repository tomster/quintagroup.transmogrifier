from zope.interface import implements

from collective.transmogrifier.interfaces import ITransmogrifier
from collective.transmogrifier.transmogrifier import _load_config, constructPipeline

from Products.GenericSetup.context import TarballExportContext, TarballImportContext
from Products.GenericSetup.interfaces import IFilesystemImporter

from quintagroup.transmogrifier.writer import WriterSection
from quintagroup.transmogrifier.reader import ReaderSection

EXPORT_CONFIG = 'export'
IMPORT_CONFIG = 'import'

def exportSiteStructure(context):
    transmogrifier = ITransmogrifier(context.getSite())

    # we don't use transmogrifer's __call__ method, because we need to do
    # some modification in pipeline sections

    transmogrifier._raw = _load_config(EXPORT_CONFIG)
    transmogrifier._data = {}

    options = transmogrifier._raw['transmogrifier']
    sections = options['pipeline'].splitlines()
    pipeline = constructPipeline(transmogrifier, sections)

    last_section = pipeline.gi_frame.f_locals['self']

    # if 'quintagroup.transmogrifier.writer' section's export context is
    # tarball replace it with given function argument
    while hasattr(last_section, 'previous'):
        if isinstance(last_section, WriterSection) and \
            isinstance(last_section.export_context, TarballExportContext):
            last_section.export_context = context
        last_section = last_section.previous
        # end cycle if we get empty starter section
        if type(last_section) == type(iter(())):
            break
        last_section = last_section.gi_frame.f_locals['self']

    # Pipeline execution
    for item in pipeline:
        pass # discard once processed

def importSiteStructure(context):
    # this function is also called when adding Plone site, so call standard handler
    if not context.readDataFile('.objects.xml', subdir='structure'):
        IFilesystemImporter(context.getSite()).import_(context, 'structure', True)
        return

    transmogrifier = ITransmogrifier(context.getSite())

    # we don't use transmogrifer's __call__ method, because we need to do
    # some modification in pipeline sections

    transmogrifier._raw = _load_config(IMPORT_CONFIG)
    transmogrifier._data = {}

    options = transmogrifier._raw['transmogrifier']
    sections = options['pipeline'].splitlines()
    pipeline = constructPipeline(transmogrifier, sections)

    last_section = pipeline.gi_frame.f_locals['self']

    # if 'quintagroup.transmogrifier.writer' section's export context is
    # tarball replace it with given function argument
    while hasattr(last_section, 'previous'):
        if isinstance(last_section, ReaderSection) and \
            isinstance(last_section.import_context, TarballImportContext):
            last_section.import_context = context
        last_section = last_section.previous
        # end cycle if we get empty starter section
        if type(last_section) == type(iter(())):
            break
        last_section = last_section.gi_frame.f_locals['self']

    # Pipeline execution
    for item in pipeline:
        pass # discard once processed


class PloneSiteImporter(object):
    """ Importer of plone site.
    """
    implements(IFilesystemImporter)

    def __init__(self, context):
        self.context = context

    def import_(self, import_context, subdir="structure", root=False):
        # When performing import steps we need to use standart importing adapter,
        # if 'object.xml' file is absent in 'structure' directory of the profile.
        # This may be because it is the base plone profile or extension profile, that has
        # structure part in other format.

        objects_xml = import_context.readDataFile('.objects.xml', subdir)
        if objects_xml is not None:
            importSiteStructure(import_context)
        else:
            from Products.CMFCore.exportimport.content import StructureFolderWalkingAdapter
            StructureFolderWalkingAdapter(self.context).import_(import_context, "structure", True)
