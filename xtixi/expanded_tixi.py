# -*- coding: utf-8 -*-
"""
Created on 24.11.2020 19:25
 
@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-24'
__all__ = ["ExpandedTixi"]

import re
import typing
try:
    # If Tixi path is specified in PYTHONPATH
    from tixi3wrapper import ReturnCode
    from tixi3wrapper import Tixi3
    from tixi3wrapper import Tixi3Exception
except ImportError:
    # This usually works in Anaconda environment
    from tixi3.tixi3wrapper import ReturnCode
    from tixi3.tixi3wrapper import Tixi3
    from tixi3.tixi3wrapper import Tixi3Exception


class ExpandedTixi(Tixi3):
    """A class providing some expanded functionalities to the tixi wrapper"""

    def __init__(self):
        super(ExpandedTixi, self).__init__()

    def xPathEvaluateNodeNumber(self, xPathExpr) -> int:
        """Return the number of paths to which the XPath resolves"""
        try:
            n = super().xPathEvaluateNodeNumber(xPathExpr)
        except Tixi3Exception as e:
            if e.code != ReturnCode.FAILED:
                raise e
            n = 0
        return n

    def xPathExpressionGetAllXPaths(self, xPathExpr) -> typing.List[str]:
        """Return a list of all XML paths to which the XPath resolves"""
        return [self.xPathExpressionGetXPath(xPathExpr, i + 1) for i in
                range(self.xPathEvaluateNodeNumber(xPathExpr))]

    @staticmethod
    def parent(xmlPath):
        """Return the parent of the input xmlPath"""
        return xmlPath.rsplit("/", 1)[0]

    @staticmethod
    def elementName(xmlPath):
        return ExpandedTixi.uniqueElementName(xmlPath).split("[")[0]

    @staticmethod
    def uniqueElementName(xmlPath):
        return xmlPath.rsplit("/", 1)[1]

    @staticmethod
    def elementNumber(xmlPath):
        elementNumberString = ExpandedTixi.uniqueElementName(xmlPath).split("[")
        if len(elementNumberString) > 1:
            return int(elementNumberString[1].rstrip("]"))
        else:
            return 1

    def elementRow(self, xmlPath):
        """Return the sequential number of the given element in its parent's tree"""
        return self.xPathExpressionGetAllXPaths(self.parent(xmlPath) + "/*").index(xmlPath) + 1
