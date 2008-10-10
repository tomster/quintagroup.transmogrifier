import os.path
from xml.dom import minidom

from zope.interface import classProvides, implements

from collective.transmogrifier.interfaces import ISection, ISectionBlueprint
from collective.transmogrifier.utils import defaultMatcher

class ManifestSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

        self.entrieskey = defaultMatcher(options, 'entries-key', name, 'entries')

    def __iter__(self):
        for item in self.previous:
            entrieskey = self.entrieskey(*item.keys())[0]
            if not entrieskey:
                yield item; continue

            manifest = self.createManifest(item[entrieskey])

            if manifest:
                files = item.setdefault('_files', {})
                item['_files']['manifest'] = {
                    'name': '.objects.xml',
                    'data': manifest,
                }

            yield item

    def createManifest(self, data):
        if not data:
            return None
        manifest = '<?xml version="1.0" ?>\n<manifest>\n'
        for obj_id, obj_type in data:
            manifest += '  <record type="%s">%s</record>\n' % (obj_type, obj_id)
        manifest += "</manifest>\n"
        return manifest

class ManifestImportSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')
        self.fileskey = defaultMatcher(options, 'files-key', name, 'files')

        # we need this dictionary to store manifest data, because reader section
        # uses recursion when walking through content folders
        self.manifests = {}

    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            fileskey = self.fileskey(*item.keys())[0]

            # skip items without path
            if not pathkey: continue

            path  = item[pathkey]

            if path != '':
                parent, item_id = os.path.split(path)
                manifest = self.manifests.get(parent, {})

                # skip that are not listed in their parent's manifest
                if item_id not in manifest: continue

                item['_type'] = manifest.pop(item_id)
                # remove empty manifest dict
                if not manifest:
                    del self.manifests[parent]

            # this item is folderish - parse manifest
            if fileskey and 'manifest' in item[fileskey]:
                self.extractManifest(path, item[fileskey]['manifest']['data'])

            yield item

    def extractManifest(self, path, data):
        doc = minidom.parseString(data)
        objects = {}
        for record in doc.getElementsByTagName('record'):
            type_ = str(record.getAttribute('type'))
            object_id = str(record.firstChild.nodeValue.strip())
            objects[object_id] = type_
        self.manifests[path] = objects
