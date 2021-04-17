# -*- coding: utf-8 -*-
"""
Created on 24.11.2020 21:14
 
@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-24'

import re
import sys
import unittest

sys.path.append("..")

try:
    # If Tixi path is specified in PYTHONPATH
    from tixi3wrapper import ReturnCode
    from tixi3wrapper import Tixi3Exception as TixiException
except ImportError:
    # This usually works in Anaconda environment
    from tixi3.tixi3wrapper import ReturnCode
    from tixi3.tixi3wrapper import Tixi3Exception as TixiException

from xtixi import Tixi

TEST_XML = """<?xml version="1.0"?>
              <root>
                  <child_1>
                      <child/>
                  </child_1>
                  <child_2 attr="foo" name="bar">
                      <child_2 attr="9">
                          <node_3>
                              <node_4/>
                              <!-- some comment -->
                              <node_4 attr="good"/>
                              <node_5>
                                    Text O
                              </node_5>
                              <node_4 name="node4">
                                    Text
                              </node_4>
                          </node_3>
                          <node_3 name="none"/>
                      </child_2>
                      <child_2/>
                      <node_3>
                          <node_4/>
                      </node_3>
                  </child_2>
                  <child_2>
                      <!-- extra comment -->
                      <node_3>
                          <node_4/>
                          <node_4/>
                          <!-- another comment -->
                          <node_5/>
                      </node_3>
                  </child_2>
              </root>
           """.strip()


class TestExpandedTixi(unittest.TestCase):
    def setUp(self):
        self.tixi = Tixi()
        # Need to get rid of leading spaces, otherwise they are treated as element #text
        string = re.sub("\s+<", "<", TEST_XML)
        self.tixi.openString(string)

    def test_xPathEvaluateNodeNumber(self):
        self.assertEqual(6, self.tixi.xPathEvaluateNodeNumber("//node_3/node_4"))
        self.assertEqual(0, self.tixi.xPathEvaluateNodeNumber("//node_3/node_9"))
        self.assertEqual(0, self.tixi.xPathEvaluateNodeNumber("//node_3/no e_9"))

    def test_xPathExpressionGetAllXPaths(self):
        self.assertEqual([
            '/root/child_2[1]/child_2[1]/node_3[1]/node_4[1]',
            '/root/child_2[1]/child_2[1]/node_3[1]/node_4[2]',
            '/root/child_2[1]/child_2[1]/node_3[1]/node_4[3]',
            '/root/child_2[1]/node_3/node_4',
            '/root/child_2[2]/node_3/node_4[1]',
            '/root/child_2[2]/node_3/node_4[2]'
        ], self.tixi.xPathExpressionGetAllXPaths("//node_3/node_4"))

        self.assertEqual([], self.tixi.xPathExpressionGetAllXPaths("//node_3/node_9"))

    def test_getAttributes(self):
        self.assertEqual({"attr": "foo", "name": "bar"}, self.tixi.getAttributes('/root/child_2[1]'))
        self.assertEqual({}, self.tixi.getAttributes('/root/child_1[1]'))

    def test_parent(self):
        self.assertEqual('/root/child_2[1]/child_2[1]/node_3[1]',
                         self.tixi.parent(
                             '/root/child_2[1]/child_2[1]/node_3[1]/node_4[2]'))
        self.assertEqual("", self.tixi.parent("/root"))
        self.assertEqual("", self.tixi.parent("/"))

    def test_elementName(self):
        self.assertEqual('node_4', self.tixi.elementName('/root/child_2[1]/child_2[1]/node_3[1]/node_4[1]'))
        self.assertEqual('child_2', self.tixi.elementName('/root/child_2[2]'))

    def test_createElement(self):
        path = self.tixi.createElement("/root/child_2[1]", "node_9")
        self.assertEqual("/root/child_2[1]/node_9", path)
        self.assertTrue(self.tixi.checkElement("/root/child_2[1]/node_9"))

    def test_xPath_by_attributeNamespace(self):
        """This test check the basic tixi functionality - not the extended tixi
        whether it can evaluate XPath expressions containing [namespace-uri()="..."]
        """

        uri = "http://some/fake/uri"
        self.tixi.declareNamespace("/root", uri, "nns")

        self.tixi.addTextAttribute('/root/child_2[1]/node_3/node_4', "nns:attr", "some namespace value")
        xpath = '//*[@*[namespace-uri()="{}"]]'.format(uri)

        self.assertEqual(['/root/child_2[1]/node_3/node_4'], self.tixi.xPathExpressionGetAllXPaths(xpath))

    def test_getUnknownNSelementPath(self):
        path = "/root/child_2[2]/node_3/node_4[2]"
        self.assertEqual("/*[1]/*[3]/*[1]/*[2]", self.tixi.getUnknownNSelementPath(path))

        # and now create some elements in namespaces

        uri1 = "www/test_uri1.html"
        uri2 = "www/test_uri2.html"
        uri3 = "www/test_uri2.html"

        self.tixi.registerNamespace(uri1, "u1")
        self.tixi.registerNamespace(uri2, "u2")
        self.tixi.registerNamespace(uri3, "u3")

        self.tixi.createElementNS("/root/child_2[1]/child_2[1]", "element_uri1", uri1)
        path = "/root/child_2[1]/child_2[1]/element_uri1"
        self.assertEqual("/*[1]/*[2]/*[1]/*[3]", self.tixi.getUnknownNSelementPath(path))

        self.tixi.createElementNS("/root/child_2[1]/child_2/node_3[1]", "element_uri2", uri2)
        # Comment node should be ignored
        path = "/root/child_2[1]/child_2[1]/node_3[1]/element_uri2"
        self.assertEqual("/*[1]/*[2]/*[1]/*[1]/*[5]", self.tixi.getUnknownNSelementPath(path))

        path = "/root/child_2[1]/child_2[1]/node_3[1]/node_4[3]"

        xmlPath = self.tixi.getUnknownNSelementPath(path)
        self.assertEqual("/*[1]/*[2]/*[1]/*[1]/*[4]", xmlPath)

        # is the path even useful?
        text = self.tixi.getTextElement(xmlPath)
        self.assertIn("Text", text)

        # Now trigger errors:

        try:
            path = self.tixi.getUnknownNSelementPath("/root/child_2[1]/child_2[1]/node_3[5]")
            self.assertFalse(True, "Should have thrown TixiException!")
        except TixiException as e:
            self.assertEqual(ReturnCode.ELEMENT_NOT_FOUND, e.code)

        try:
            path = self.tixi.getUnknownNSelementPath("/root/child_2/child_2[1]/node_3[5]")
            self.assertFalse(True, "Should have thrown TixiException!")
        except TixiException as e:
            self.assertEqual(ReturnCode.ELEMENT_PATH_NOT_UNIQUE, e.code)

        try:
            path = self.tixi.getUnknownNSelementPath("blah!")
            self.assertFalse(True, "Should have thrown TixiException!")
        except TixiException as e:
            self.assertEqual(ReturnCode.INVALID_XPATH, e.code)

    def test_getURI(self):
        # First, set some namespaces

        uri1 = "http://www.test_uri1"
        uri2 = "http://www.test_uri2"
        # This is needed only to effectively set namespaces
        self.tixi.registerNamespace(uri1, "u_test1")
        self.tixi.registerNamespace(uri2, "u_test2")

        self.tixi.setElementNamespace("/root/child_2[1]/child_2[1]/node_3[1]/node_4[2]", uri2, None)
        self.tixi.setElementNamespace("/root/child_2[1]", uri1, None)

        uri1_path, uri1 = self.tixi.getURI("/root/child_2[1]/child_2[1]")
        uri2_path, uri2 = self.tixi.getURI("/root/child_2[1]/child_2[1]/node_3[1]/node_4[2]")
        uri3_path, uri3 = self.tixi.getURI('/root/child_2[2]/node_3/node_4[2]')

        # Test the function
        self.assertEqual(("/root/child_2[1]", "http://www.test_uri1"), (uri1_path, uri1))
        self.assertEqual(("/root/child_2[1]/child_2[1]/node_3[1]/node_4[2]", "http://www.test_uri2"),
                         (uri2_path, uri2))
        self.assertEqual((None, None), (uri3_path, uri3))

        # try accessing the nodes
        self.tixi.registerNamespace(uri1, "u1")
        self.tixi.registerNamespace(uri2, "u2")

        self.assertTrue(self.tixi.checkElement("/root"))
        self.assertTrue(self.tixi.checkElement("/root/u1:child_2[1]"))
        self.assertTrue(self.tixi.checkElement("/root/u_test1:child_2[1]"))
        self.assertTrue(self.tixi.checkElement("/root/u1:child_2[1]/child_2[1]"))
        self.assertTrue(self.tixi.checkElement("/root/u1:child_2[1]/child_2[1]/node_3[1]"))
        # There's only one node_4 in namespace u2
        self.assertTrue(self.tixi.checkElement("/root/u1:child_2[1]/child_2[1]/node_3[1]/u2:node_4[1]"))
        self.assertEqual("foo", self.tixi.getTextAttribute("/root/u1:child_2[1]", "attr"))
        self.assertEqual("good",
                         self.tixi.getTextAttribute("/root/u1:child_2[1]/child_2[1]/node_3[1]/u2:node_4[1]", "attr"))

    def test_addTextElement(self):
        path = self.tixi.addTextElement("/root/child_2[1]", "node_9", "text of the node")
        self.assertEqual("/root/child_2[1]/node_9", path)
        self.assertTrue(self.tixi.checkElement("/root/child_2[1]/node_9"))
        self.assertEqual("text of the node", self.tixi.getTextElement(path))

    def test_createElementAtIndex(self):
        path = self.tixi.createElementAtIndex("/root/child_2[1]", "node_9", 2)
        self.assertEqual("/root/child_2[1]/node_9", path)
        self.assertTrue(self.tixi.checkElement("/root/child_2[1]/node_9"))
        self.assertEqual("node_9", self.tixi.getChildNodeName("/root/child_2[1]", 2))

    def test_createElementNS(self):
        uri = "http://www.testtixi.uri"

        path = self.tixi.createElementNS("/root/child_2[2]/node_3", "new", uri)
        self.assertEqual('/root/child_2[2]/node_3/*[4]', path)

    def test_createElementNSAtIndex(self):
        uri = "http://www.testtixi.uri"
        self.tixi.registerNamespace(uri, "tu")
        path = self.tixi.createElementNSAtIndex("/root/child_2[2]/node_3", "new", 2, uri)
        self.assertEqual("/root/child_2[2]/node_3/*[2]", path)

    def test_addTextElementAtIndex(self):
        path = self.tixi.addTextElementAtIndex("/root/child_2[1]", "node_9", "text of the node", 2)
        self.assertEqual("/root/child_2[1]/node_9", path)
        self.assertTrue(self.tixi.checkElement("/root/child_2[1]/node_9"))
        self.assertEqual("text of the node", self.tixi.getTextElement(path))
        self.assertEqual("node_9", self.tixi.getChildNodeName("/root/child_2[1]", 2))

    def test_uniqueElementName(self):
        self.assertEqual('node_4[1]', self.tixi.uniqueElementName('/root/child_2[1]/child_2[1]/node_3[1]/node_4[1]'))
        self.assertEqual('node_3[1]', self.tixi.uniqueElementName('/root/child_2[1]/node_3[1]'))
        self.assertEqual('node_3', self.tixi.uniqueElementName('/root/child_2[1]/node_3'))
        self.assertEqual('child_2[2]', self.tixi.uniqueElementName('/root/child_2[2]'))

    def test_elementNumber(self):
        self.assertEqual(1, self.tixi.elementNumber('/root/child_1'))
        self.assertEqual(1, self.tixi.elementNumber('/root/child_2[1]'))
        self.assertEqual(1, self.tixi.elementNumber('/root/child_2[1]/child_2[1]/node_3[1]/node_5'))
        self.assertEqual(2, self.tixi.elementNumber('/root/child_2[2]'))

    def test_elementRow(self):
        self.assertEqual(1, self.tixi.elementRow('/root/child_1'))
        self.assertEqual(2, self.tixi.elementRow('/root/child_2[1]'))
        self.assertEqual(3, self.tixi.elementRow('/root/child_2[1]/child_2[1]/node_3[1]/node_5'))
        self.assertEqual(3, self.tixi.elementRow('/root/child_2[2]'))

    def test_findInheritedAttribute(self):
        self.assertEqual("/root/child_2[1]/child_2[1]/node_3[1]/node_4[2]",
                         self.tixi.findInheritedAttribute("/root/child_2[1]/child_2[1]/node_3[1]/node_4[2]", "attr"))
        self.assertEqual("/root/child_2[1]",
                         self.tixi.findInheritedAttribute("/root/child_2[1]/node_3/node_4", "attr"))
        self.assertEqual("/root/child_2[1]/child_2[1]",
                         self.tixi.findInheritedAttribute("/root/child_2[1]/child_2[1]/node_3[1]/node_4[1]", "attr"))
        self.assertIsNone(self.tixi.findInheritedAttribute("/root/child_1/child", "attr"))

    def test_getInheritedTextAttribute(self):
        self.assertEqual("good",
                         self.tixi.getInheritedTextAttribute("/root/child_2[1]/child_2[1]/node_3[1]/node_4[2]", "attr"))
        self.assertEqual("foo",
                         self.tixi.getInheritedTextAttribute("/root/child_2[1]/node_3/node_4", "attr"))
        self.assertEqual("9",
                         self.tixi.getInheritedTextAttribute("/root/child_2[1]/child_2[1]/node_3[1]/node_4[1]", "attr"))
        self.assertIsNone(self.tixi.getInheritedTextAttribute("/root/child_1/child", "attr"))

    def test_clearComments(self):
        paths = ["/root/child_2[1]/child_2[1]/node_3[1]",
                            "/root/child_2[2]","/root/child_2[2]/node_3"
                            ]
        nums = [2,1,3]
        for path, i in zip(paths, nums):
            self.assertEqual("#comment", self.tixi.getChildNodeName(path, i))
        self.tixi.clearComments()
        for path, i in zip(paths, nums):
            self.assertNotEqual("#comment", self.tixi.getChildNodeName(path, i))
        self.assertEqual([], self.tixi.xPathExpressionGetAllXPaths("//comment()"))


if __name__ == '__main__':
    unittest.main()
