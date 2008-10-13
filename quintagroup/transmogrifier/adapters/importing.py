from xml.dom import minidom

from zope.interface import implements
from zope.component import adapts

from Products.Archetypes.interfaces import IBaseObject
from Products.Archetypes import atapi

from quintagroup.transmogrifier.interfaces import IImportDataCorrector

EXISTING_UIDS = {}
REFERENCE_QUEUE = {}

class ReferenceImporter(object):
    """ Demarshall content from xml file by using of Marshall product.
    """
    implements(IImportDataCorrector)
    adapts(IBaseObject)

    def __init__(self, context):
        self.context = context

    def __call__(self, data):
        data['data'] = self.importReferences(data['data'])
        EXISTING_UIDS[self.context.UID()] = None
        return data

    def importReferences(self, data):
        """ Marshall 1.0.0 doesn't import references, do it manually.
        """
        doc = minidom.parseString(data)
        root = doc.documentElement
        for fname in self.context.Schema().keys():
            if not isinstance(self.context.Schema()[fname], atapi.ReferenceField):
                continue
            uids = []
            validUIDs = True
            elements = [i for i in root.getElementsByTagName('field') if i.getAttribute('name') == fname]
            if not elements:
                # if needed elements are absent skip this field
                # update as much as posible fields and don't raise exceptions
                continue
            elem = elements[0]
            for uid_elem in elem.getElementsByTagName('uid'):
                value = str(uid_elem.firstChild.nodeValue)
                uids.append(value)
                if value not in EXISTING_UIDS:
                    validUIDs = False
            if validUIDs and uids:
                mutator = self.context.Schema()[fname].getMutator(self.context)
                mutator(uids)
            elif uids:
                suid = str(root.getElementsByTagName('uid')[0].firstChild.nodeValue.strip())
                REFERENCE_QUEUE[suid] = {}
                REFERENCE_QUEUE[suid][fname] = uids
            root.removeChild(elem)
        return doc.toxml('utf-8')

class FileImporter(ReferenceImporter):
    """ Update file fields from XML data, generated by Marshall product.
    """
    implements(IImportDataCorrector)

    def __call__(self, data):
        xml = data['data']
        xml = self.updateFileFields(xml)
        data['data'] = self.importReferences(xml)
        return data

    def updateFileFields(self, data):
        """ Update 'file' or 'image' field of instance, remove corresponding
            element and return resulting xml.
        """
        doc = minidom.parseString(data)
        root = doc.documentElement
        # there is only one 'field' element with name 'file' or 'image'
        elem = [i for i in root.getElementsByTagName('field') 
                     if i.getAttribute('name') in ('file', 'image')][0]

        value = elem.firstChild.nodeValue
        value = value.decode(elem.getAttribute('transfer_encoding'))
        # why it's named 'content_type' but not 'mimetype'?
        ct = elem.getAttribute('content_type')
        fn = elem.getAttribute('filename')

        mutator = self.context.Schema()[elem.getAttribute('name')].getMutator(self.context)
        mutator(value, filename=fn, mimetype=ct) #, **kw)

        # remove element and return result xml
        root.removeChild(elem)
        return doc.toxml('utf-8')