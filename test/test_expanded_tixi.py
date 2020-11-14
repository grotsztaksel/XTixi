# -*- coding: utf-8 -*-
"""
Created on 24.11.2020 21:14
 
@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-24'

import re
import unittest

from tixi3wrapper import ReturnCode
from tixi3wrapper import Tixi3Exception

from xtixi.expanded_tixi import ExpandedTixi

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
                      <node_3>
                          <node_4/>
                          <node_4/>
                          <node_5/>
                      </node_3>
                  </child_2>
              </root>
           """.strip()


class TestExpandedTixi(unittest.TestCase):
    def setUp(self):
        self.tixi = ExpandedTixi()
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

    def test_parent(self):
        self.assertEqual('/root/child_2[1]/child_2[1]/node_3[1]',
                         self.tixi.parent(
                             '/root/child_2[1]/child_2[1]/node_3[1]/node_4[2]'))
        self.assertEqual("", self.tixi.parent("/root"))
        self.assertEqual("", self.tixi.parent("/"))

    def test_elementName(self):
        self.assertEqual('node_4', self.tixi.elementName('/root/child_2[1]/child_2[1]/node_3[1]/node_4[1]'))
        self.assertEqual('child_2', self.tixi.elementName('/root/child_2[2]'))

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


if __name__ == '__main__':
    unittest.main()
