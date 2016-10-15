from zope.component.hooks import getSite


def sitePath(site=None):
    site = site or getSite()
    return site.getPhysicalPath()


def parentPath(path):
    return '/'.join(path.split('/')[:-1])


def traversable(path):
    base = sitePath()
    


