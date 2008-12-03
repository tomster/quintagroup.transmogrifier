import traceback
from xml.dom import minidom

from zope.interface import classProvides, implements

from ZODB.POSException import ConflictError

from Products.Archetypes.interfaces import IBaseObject

from collective.transmogrifier.interfaces import ISection, ISectionBlueprint
from collective.transmogrifier.utils import defaultMatcher

class FileExporterSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')
        self.fileskey = options.get('files-key', '_files').strip()
        # only this section can add 'excluded_field' for marshalling
        #self.excludekey = defaultMatcher(options, 'exclude-key', name, 'excluded_fields')
        self.excludekey = options.get('exclude-key', '_excluded_fields').strip()

    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]

            if not pathkey:
                yield item; continue

            path = item[pathkey]
            obj = self.context.unrestrictedTraverse(path, None)
            if obj is None:         # path doesn't exist
                yield item; continue

            if IBaseObject.providedBy(obj):
                schema = obj.Schema()
                binary_fields = {}
                binary_field_names = []
                for field in schema.keys():
                    if obj.isBinary(field):
                        fname, ct, data = self.extractFile(obj, field)
                        binary_field_names.append(field)
                        if fname == '' or data == '':
                            # empty file fields have empty filename and empty data
                            # skip them
                            continue
                        binary_fields[field] = dict(filename=fname, mimetype=ct)
                        files = item.setdefault(self.fileskey, {})
                        #key = "field-%s" % field
                        files[fname] = {
                            # now we export FileField as file with it's original name,
                            # but it may cause name collapse
                            'name': fname,
                            'data': data,
                            'content_type': ct,
                        }
                if binary_fields:
                    files['file-fields'] = {
                        'name': '.file-fields.xml',
                        'data': self.createManifest(binary_fields),
                    }
                if binary_field_names:
                    item[self.excludekey] = binary_field_names

            yield item

    def extractFile(self, obj, field):
        """ Return tuple of (filename, content_type, data)
        """
        field = obj.getField(field)
        base_unit = field.getBaseUnit(obj)
        fname = base_unit.getFilename() 
        ct = base_unit.getContentType()
        value = base_unit.getRaw()

        return fname, ct, value

    def createManifest(self, binary_fields):
        manifest = '<?xml version="1.0" ?>\n<manifest>\n'
        for field, info in binary_fields.items():
            manifest += '  <field name="%s">\n' % field
            manifest += '    <filename>%s</filename>\n' % info['filename']
            manifest += '    <mimetype>%s</mimetype>\n' % info['mimetype']
            manifest += '  </field>\n'
        manifest += "</manifest>\n"
        return manifest

class FileImporterSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

        self.pathkey = defaultMatcher(options, 'path-key', name, 'path')
        self.fileskey = defaultMatcher(options, 'files-key', name, 'files')
        self.contextkey = defaultMatcher(options, 'context-key', name, 'import_context')

    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            fileskey = self.fileskey(*item.keys())[0]
            contextkey = self.contextkey(*item.keys())[0]

            if not (pathkey and fileskey):
                yield item; continue
            if 'file-fields' not in item[fileskey]:
                yield item; continue

            path = item[pathkey]
            obj = self.context.unrestrictedTraverse(path, None)
            if obj is None:         # path doesn't exist
                yield item; continue

            if IBaseObject.providedBy(obj):
                try:
                    manifest = item[fileskey]['file-fields']['data']
                    for field, info in self.parseManifest(manifest).items():
                        fname = info['filename']
                        ct = info['mimetype']
                        if fname in item[fileskey]:
                            data = item[fileskey][fname]['data']
                        elif contextkey:
                            data = context.readDataFile("%s/%s" % (path, fname))
                            if data is None:
                                continue
                        mutator = obj.getField(field).getMutator(obj)
                        mutator(data, filename=fname, mimetype=ct)
                except ConflictError:
                    raise
                except Exception, e:
                    print "Exception in fileimporter section:"
                    print '-'*60
                    traceback.print_exc()
                    print '-'*60

            yield item

    def parseManifest(self, manifest):
        doc = minidom.parseString(manifest)
        fields = {}
        for elem in doc.getElementsByTagName('field'):
            field = fields.setdefault(str(elem.getAttribute('name')), {})
            for child in elem.childNodes:
                if child.nodeType != child.ELEMENT_NODE:
                    continue
                if child.tagName == u'filename':
                    field['filename'] = child.firstChild.nodeValue.strip().encode('utf-8')
                elif child.tagName == u'mimetype':
                    field['mimetype'] = str(child.firstChild.nodeValue.strip())

        return fields
