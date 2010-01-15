from xml.dom import minidom

from zope.interface import classProvides, implements, providedBy
from zope.component import getUtilitiesFor, queryMultiAdapter

from plone.portlets.interfaces import ILocalPortletAssignable, IPortletManager,\
    IPortletAssignmentMapping
from plone.portlets.constants import CONTEXT_CATEGORY
from plone.app.portlets.interfaces import IPortletTypeInterface
from plone.app.portlets.exportimport.interfaces import IPortletAssignmentExportImportHandler

from collective.transmogrifier.interfaces import ISection, ISectionBlueprint
from collective.transmogrifier.utils import defaultMatcher

class PortletsExporterSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')
        self.fileskey = options.get('files-key', '_files').strip()

        self.doc = minidom.Document()

    def __iter__(self):
        self.portlet_schemata = dict([(iface, name,) for name, iface in 
            getUtilitiesFor(IPortletTypeInterface)])
        self.portlet_managers = getUtilitiesFor(IPortletManager)

        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]

            if not pathkey:
                yield item; continue

            path = item[pathkey]
            obj = self.context.unrestrictedTraverse(path, None)
            if obj is None:         # path doesn't exist
                yield item; continue

            if ILocalPortletAssignable.providedBy(obj):
                data = None

                root = self.doc.createElement('portlets')
                for elem in self.exportAssignments(obj):
                    root.appendChild(elem)
                #for elem in self.exportBlacklists(obj)
                    #root.appendChild(elem)
                if root.hasChildNodes():
                    self.doc.appendChild(root)
                    data = self.doc.toprettyxml(indent='  ', encoding='utf-8')
                    self.doc.unlink()

                if data:
                    files = item.setdefault(self.fileskey, {})
                    item[self.fileskey]['portlets'] = {
                        'name': '.portlets.xml',
                        'data': data,
                    }
            yield item

    def exportAssignments(self, obj):
        assignments = []
        for manager_name, manager in self.portlet_managers:
            mapping = queryMultiAdapter((obj, manager), IPortletAssignmentMapping)
            mapping = mapping.__of__(obj)

            for name, assignment in mapping.items():
                type_ = None
                for schema in providedBy(assignment).flattened():
                    type_ = self.portlet_schemata.get(schema, None)
                    if type_ is not None:
                        break

                if type_ is not None:
                    child = self.doc.createElement('assignment')
                    child.setAttribute('manager', manager_name)
                    child.setAttribute('category', CONTEXT_CATEGORY)
                    child.setAttribute('key', '/'.join(obj.getPhysicalPath()))
                    child.setAttribute('type', type_)
                    child.setAttribute('name', name)

                    assignment = assignment.__of__(mapping)
                    # use existing adapter for exporting a portlet assignment
                    handler = IPortletAssignmentExportImportHandler(assignment)
                    handler.export_assignment(schema, self.doc, child)

                    assignments.append(child)

        return assignments

class PortletsImporterSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')
        self.fileskey = defaultMatcher(options, 'files-key', name, 'files')

    def __iter__(self):

        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            fileskey = self.fileskey(*item.keys())[0]

            if not (pathkey and fileskey):
                yield item; continue
            if 'portlets' not in item[fileskey]:
                yield item; continue

            path = item[pathkey]
            obj = self.context.unrestrictedTraverse(path, None)
            if obj is None:         # path doesn't exist
                yield item; continue

            #if ILocalPortletAssignable.providedBy(obj):
                #data = None
                #data = item[fileskey]['portlets']['data']
                #doc = minidom.parseString(data)
                #root = doc.documentElement
                #children = [k for k in root.childNodes]
                #for child in children:
                    #if child.nodeName != 'assignment':
                        #continue
                    #self.importPortlet(child)

            yield item
