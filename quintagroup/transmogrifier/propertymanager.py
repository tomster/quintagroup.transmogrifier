from xml.dom import minidom

from zope.interface import classProvides, implements

from collective.transmogrifier.interfaces import ISection, ISectionBlueprint
from collective.transmogrifier.utils import defaultMatcher

from OFS.interfaces import IPropertyManager
from Products.GenericSetup.utils import PropertyManagerHelpers, NodeAdapterBase

class Helper(PropertyManagerHelpers, NodeAdapterBase):
    """ We need this class because PropertyManagerHelpers in _initProperties
        method uses _convertToBoolean and _getNodeText methods from
        NodeAdapterBase class.
    """
    def __init__(self):
        pass

class PropertiesExporterSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')
        self.fileskey = options.get('files-key', '_files').strip()

        self.excludekey = defaultMatcher(options, 'exclude-key', name, 'excluded_properties')
        self.exclude = filter(None, [i.strip() for i in 
                              options.get('exclude', '').splitlines()])

        self.helper = Helper()
        self.doc = minidom.Document()
        self.helper._doc = self.doc

    def __iter__(self):
        helper = self.helper
        doc = self.doc

        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]

            if not pathkey:
                yield item; continue

            path = item[pathkey]
            obj = self.context.unrestrictedTraverse(path, None)
            if obj is None:         # path doesn't exist
                yield item; continue

            if IPropertyManager.providedBy(obj):
                data = None
                excludekey = self.excludekey(*item.keys())[0]
                excluded_props = tuple(self.exclude)
                if excludekey:
                    excluded_props = tuple(set(item[excludekey]) | set(excluded_props))

                helper.context = obj
                node = doc.createElement('properties')
                for elem in helper._extractProperties().childNodes:
                    if elem.nodeName != 'property':
                        continue
                    if elem.getAttribute('name') not in excluded_props:
                        node.appendChild(elem)
                if node.hasChildNodes():
                    doc.appendChild(node)
                    data = doc.toprettyxml(indent='  ', encoding='utf-8')
                    doc.unlink()

                if data:
                    files = item.setdefault(self.fileskey, {})
                    item[self.fileskey]['propertymanager'] = {
                        'name': '.properties.xml',
                        'data': data,
                    }

            yield item

class PropertiesImporterSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')
        self.fileskey = defaultMatcher(options, 'files-key', name, 'files')

        self.excludekey = defaultMatcher(options, 'exclude-key', name, 'excluded_properties')
        self.exclude = filter(None, [i.strip() for i in 
                            options.get('exclude', '').splitlines()])

        self.helper = Helper()
        self.helper._encoding = 'utf-8'

    def __iter__(self):
        helper = self.helper

        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            fileskey = self.fileskey(*item.keys())[0]

            if not (pathkey and fileskey):
                yield item; continue
            if 'propertymanager' not in item[fileskey]:
                yield item; continue

            path = item[pathkey]
            obj = self.context.unrestrictedTraverse(path, None)
            if obj is None:         # path doesn't exist
                yield item; continue

            if IPropertyManager.providedBy(obj):
                data = None
                excludekey = self.excludekey(*item.keys())[0]
                excluded_props = self.exclude
                if excludekey:
                    excluded_props = tuple(set(item[excludekey]) | set(excluded_props))

                data = item[fileskey]['propertymanager']['data']
                doc = minidom.parseString(data)
                root = doc.documentElement
                for child in root.childNodes:
                    if child.nodeName != 'property':
                        continue
                    if child.getAttribute('name') in excluded_props:
                        root.removeChild(child)

                helper.context = obj
                helper._initProperties(root)

            yield item
