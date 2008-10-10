try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)

# import monkey pathes for GS TarballExportContext
import patches

def initialize(context):
    """Initializer called when used as a Zope 2 product."""
