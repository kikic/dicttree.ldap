from dicttree.ldap.tests import mixins


class TestNodeAttrs(mixins.Slapd):
    def test_attrs(self):
        node = self.dir[somedn]
        node.attrs['cn'] -> ['cn0']
        node.attrs['objectClass'] -> ['organizationalRole']
        node.attrs[somenew] = 'abc'
