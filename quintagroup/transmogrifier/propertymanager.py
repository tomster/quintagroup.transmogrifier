from xml.dom import minidom

from zope.interface import classProvides, implements

from collective.transmogrifier.interfaces import ISection, ISectionBlueprint
from collective.transmogrifier.utils import defaultMatcher

from OFS.interfaces import IPropertyManager
from Products.GenericSetup.utils import PropertyManagerHelpers

class PropertyManagerSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')
        self.excludekey = defaultMatcher(options, 'exclude-key', name, 'excluded_properties')
        if 'exclude' in options:
            self.exclude = [i.strip() for i in options['exclude'].splitlines() if i.strip()]
        else:
            self.exclude = []

        self.helper = PropertyManagerHelpers()
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
                excluded_props = self.exclude
                if excludekey:
                    excluded_props = tuple(set(item[excludekey]) | set(excluded_props))

                helper.context = obj
                node = doc.createElement('properties')
                for elem in helper._extractProperties().childNodes:
                    if elem.getAttribute('name') not in excluded_props:
                        node.appendChild(elem)
                if node.hasChildNodes():
                    doc.appendChild(node)
                    data = doc.toprettyxml(indent='  ', encoding='utf-8')
                    doc.unlink()

                if data:
                    files = item.setdefault('_files', {})
                    item['_files']['propertymanager'] = {
                        'name': '.properties.xml',
                        'data': data,
                    }

            yield item
