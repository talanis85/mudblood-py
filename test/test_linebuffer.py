import unittest

from linebuffer import AString,Linebuffer

class TestAString(unittest.TestCase):
    def test_create(self):
        a = AString("test")
        self.assertEqual(str(a), "test")
        b = AString("\n")
        self.assertEqual(str(b), "\n")

    def test_compare(self):
        a = AString("test")
        b = AString("foo")
        self.assertTrue(a != b)
        self.assertTrue(a > b)

    def test_add(self):
        a = AString("test")
        b = AString("foo")
        ab = a + b
        self.assertEqual(str(ab), "testfoo")
        self.assertEqual(a + "", a)

    def test_splitlines(self):
        c = AString("test")
        self.assertEqual([x for x in c.splitLines()], ["test"])

        c += "\nfoo"
        self.assertEqual([x for x in c.splitLines()], ["test", "foo"])
        
        c += "\n\n"
        self.assertEqual([x for x in c.splitLines()], ["test", "foo", "", ""])

class TestLinebuffer(unittest.TestCase):
    def test_empty(self):
        lb = Linebuffer()
        self.assertEqual(lb.render(30, 0, 30), [""])

    def test_render(self):
        lb = Linebuffer()
        lb.append("hallo\nwelt\n")
        self.assertEqual(lb.render(30, 0, 30), ["hallo", "welt", ""])

    def test_append(self):
        lb = Linebuffer()
        lb.append("test")
        self.assertEqual(lb.render(30, 0, 30), ["test"])
        lb.append("\n")
        self.assertEqual(lb.render(30, 0, 30), ["test", ""])

    def test_update(self):
        lb = Linebuffer()
        lb.append("test")
        lb.update()
        self.assertEqual(lb.render(30, 0, 30), ["test"])

        lb.append("\n")
        lb.update()
        self.assertEqual(lb.render(30, 0, 30), ["test", ""])

        lb.append("foo\n")
        lb.update()
        self.assertEqual(lb.render(30, 0, 30), ["test", "foo", ""])

        lb.append("\n\n")
        lb.update()
        self.assertEqual(lb.render(30, 0, 30), ["test", "foo", "", "", ""])


suite = unittest.TestSuite([unittest.TestLoader().loadTestsFromTestCase(x) for x in
    [TestAString, TestLinebuffer]
    ])
