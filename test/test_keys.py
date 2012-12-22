import unittest

from mudblood import keys

class TestKeys(unittest.TestCase):
    def setUp(self):
        self.b = keys.Bindings()

    def test_add(self):
        self.b.add((keys.KEY_F1, keys.KEY_CTRL_TILDE, keys.KEY_BACKSPACE), "value1")
        self.assertTrue(self.b.key(keys.KEY_F1))
        self.assertTrue(self.b.key(keys.KEY_CTRL_TILDE))
        self.assertTrue(self.b.key(keys.KEY_BACKSPACE) == "value1")
        self.b.reset()
        self.assertTrue(self.b.key(keys.KEY_F1))
        self.assertTrue(self.b.key(keys.KEY_CTRL_TILDE))
        self.assertFalse(self.b.key(ord('b')))
        self.b.reset()
        self.assertFalse(self.b.key(ord('a')))

    def test_delete(self):
        self.b.add((ord('a')), "value1")
        self.b.delete((ord('a')))
        self.assertFalse(self.b.key(ord('a')))

    def test_parse(self):
        self.b.add(self.b.parse("<E><F1>a"), "value1")
        self.assertTrue(self.b.key(ord("\\")))
        self.assertTrue(self.b.key(keys.KEY_F1))
        self.assertTrue(self.b.key(ord('a')) == "value1")
        self.b.delete(self.b.parse("<E><F1>a"))
        self.assertFalse(self.b.key(ord("\\")))
        self.assertFalse(self.b.key(keys.KEY_F1))
        self.assertFalse(self.b.key(ord('a')) == "value1")


suite = unittest.TestSuite([unittest.TestLoader().loadTestsFromTestCase(x) for x in
    [TestKeys]
    ])
