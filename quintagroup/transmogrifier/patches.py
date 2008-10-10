import os
import time
from tarfile import TarInfo, DIRTYPE
from StringIO import StringIO

# TarballExportContext don't write dirs in tarball and we need to fix this

#security.declareProtected( ManagePortal, 'writeDataFile' )
def writeDataFile( self, filename, text, content_type, subdir=None ):

    """ See IExportContext.
    """
    mod_time = time.time()

    if subdir is not None:
        elements = subdir.split('/')
        parents = filter(None, elements)
        while parents:
            dirname = os.path.join(*parents)
            try:
                self._archive.getmember(dirname+'/')
            except KeyError:
                info = TarInfo(dirname)
                info.size = 0
                info.mtime = mod_time
                info.type = DIRTYPE
                self._archive.addfile(info, StringIO())
            parents = parents[:-1]

        filename = '/'.join( ( subdir, filename ) )

    stream = StringIO( text )
    info = TarInfo( filename )
    info.size = len( text )
    info.mtime = mod_time
    self._archive.addfile( info, stream )

from Products.GenericSetup.context import TarballExportContext
TarballExportContext.writeDataFile = writeDataFile

from Products.GenericSetup.context import SKIPPED_FILES, SKIPPED_SUFFIXES

def listDirectory(self, path, skip=SKIPPED_FILES,
                    skip_suffixes=SKIPPED_SUFFIXES):

    """ See IImportContext.
    """
    if path is None:  # root is special case:  no leading '/'
        path = ''
    elif path:
        if not self.isDirectory(path):
            return None

        if not path.endswith('/'):
            path = path + '/'

    pfx_len = len(path)

    names = []
    for name in self._archive.getnames():
        if name == path or not name.startswith(path):
            continue
        name = name[pfx_len:]
        if name.count('/') > 1:
            continue
        if '/' in name and not name.endswith('/'):
            continue
        if name in skip:
            continue
        if [s for s in skip_suffixes if name.endswith(s)]:
            continue
        # directories have trailing '/' character and we need to remove it
        name.rstrip('/')
        names.append(name)

    return names

from Products.GenericSetup.context import TarballImportContext
TarballImportContext.listDirectory = listDirectory
