import unittest

from dicttree.ldap.tests import mixins

class TestNodeAttrs(mixins.Slapd, unittest.TestCase):
    ENTRIES = {
        'cn=cn0,o=o': (('cn', ['cn0']),
                       ('objectClass', ['organizationalRole'])),
        'cn=cn1,o=o': (('cn', 'cn1'),
                       ('objectClass', ['organizationalRole'])),
    }
    ADDITIONAL = {
        'cn=cn2,o=o': (('cn', ['cn2']),
                       ('objectClass', ['organizationalRole'])),
    }

    def test_getitem(self):
        node = self.dir['cn=cn0,o=o']
        self.assertEqual(node.attrs['cn'], ['cn0'])
        self.assertEqual(node.attrs['objectClass'], ['organizationalRole'])
        def fail():
            node.attrs['fail']
        self.assertRaises(KeyError, fail)

    def test_contains(self):
        node = self.dir['cn=cn0,o=o']
        self.assertTrue('cn' in node.attrs)
        self.assertTrue('objectClass' in node.attrs)
        self.assertFalse('fail' in node.attrs)

    def test_iter(self):
        node = self.dir['cn=cn0,o=o']
        self.assertItemsEqual(node.attrs, ['objectClass', 'cn'])

    def test_del(self):
        node = self.dir['cn=cn0,o=o']
        node.attrs['description'] = 'abc'
        self.assertItemsEqual(node.attrs, ['objectClass', 'cn', 'description'])
        del node.attrs['description']
        self.assertItemsEqual(node.attrs, ['objectClass', 'cn'])

    def test_setitem(self):
        node = self.dir['cn=cn0,o=o']
        node.attrs['description'] = 'abc'
        self.assertEqual(len(node.attrs), 3)
        self.assertEqual(node.attrs['description'], ['abc'])
        self.assertItemsEqual(node.attrs, ['objectClass', 'cn', 'description'])
        node.attrs['description'] = 'aaa'
        self.assertEqual(node.attrs['description'], ['aaa'])
