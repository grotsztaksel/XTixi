# -*- coding: utf-8 -*-
"""
Created on 24.11.2020 19:25
 
@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-24'
__all__ = ["ExpandedTixi"]

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

import typing

class ExpandedTixi(Tixi3):
    """A class providing some expanded functionalities to the tixi wrapper"""

    def __init__(self):
        super(ExpandedTixi, self).__init__()

    #
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

    #
    def getAttributes(self, element_path) -> typing.Dict[str, str]:
        """
        Return a list of all attributes of a given element
        :param element_path: XML path of the element
        :return: dict with attribute names as keys and their values as values
        """
        attributes = dict()
        for i in range(self.getNumberOfAttributes(element_path)):
            attrName = self.getAttributeName(element_path, i + 1)
            attrValue = self.getTextAttribute(element_path, attrName)
            attributes[attrName] = attrValue
        return attributes

    #
    @staticmethod
    def parent(xmlPath) -> str:
        """Return the parent of the input xmlPath"""
        return xmlPath.rsplit("/", 1)[0]

    #
    @staticmethod
    def elementName(xmlPath) -> str:
        return ExpandedTixi.uniqueElementName(xmlPath).split("[")[0]

    #
    @staticmethod
    def uniqueElementName(xmlPath) -> str:
        return xmlPath.rsplit("/", 1)[1]

    #
    @staticmethod
    def elementNumber(xmlPath) -> int:
        elementNumberString = ExpandedTixi.uniqueElementName(xmlPath).split("[")
        if len(elementNumberString) > 1:
            return int(elementNumberString[1].rstrip("]"))
        else:
            return 1

    #
    def elementRow(self, xmlPath) -> int:
        """Return the sequential number of the given element in its parent's tree"""
        return self.xPathExpressionGetAllXPaths(self.parent(xmlPath) + "/*").index(xmlPath) + 1

    def createElement(self, xmlPath, elementName) -> str:
        """Create an element and return its path"""
        super().createElement(xmlPath, elementName)
        return self.xPathExpressionGetAllXPaths("{}/{}".format(xmlPath, elementName))[-1]

    def createElementAtIndex(self, xmlPath, elementName, index) -> str:
        """Create an element at given index and return its path"""
        super().createElementAtIndex(xmlPath, elementName, index)
        return self.xPathExpressionGetXPath(xmlPath + "/*", index)

    #
    def createElementNS(self, xmlPath, elementName, uri, prefix=None) -> str:
        """Create an element using namespace and return its path, if a prefix is known"""
        super().createElementNS(xmlPath, elementName, uri)
        return self.xPathExpressionGetAllXPaths("{}/*".format(xmlPath))[-1]

    def createElementNSAtIndex(self, xmlPath, elementName, index, uri) -> str:
        """Create an element at given index using namespace and return its path"""
        super().createElementNSAtIndex(xmlPath, elementName, index, uri)
        return self.xPathExpressionGetXPath(xmlPath + "/*", index)

    def addTextElement(self, xmlPath, elementName, text) -> str:
        """Create a text element and return its path"""
        super().addTextElement(xmlPath, elementName, text)
        return self.xPathExpressionGetAllXPaths("{}/{}".format(xmlPath, elementName))[-1]

    def addTextElementAtIndex(self, xmlPath, elementName, text, index) -> str:
        """Create a text element and return its path"""
        super().addTextElementAtIndex(xmlPath, elementName, text, index)
        return self.xPathExpressionGetXPath(xmlPath + "/*", index)

    def findInheritedAttribute(self, xmlPath, attrName) -> typing.Union[str, None]:
        """Find the "youngest" parent - or self that has the required attribute and return its path.
           If none of the parent elements has the required attribute, return empty string
        """

        if self.checkAttribute(xmlPath, attrName):
            return xmlPath

        path = xmlPath
        while path and not self.checkAttribute(path, attrName):
            path = self.parent(path)
        if not path:
            return None
        return path

        # XPath approach does not return expected results. A bug in Tixi3?
        xpath = "{}[ancestor-or-self::*[@{}]]".format(xmlPath, attrName)
        try:
            return self.xPathExpressionGetXPath(xpath, 1)
        except Tixi3Exception as e:
            if e.code != ReturnCode.FAILED:
                raise e
            return None

    #
    def getInheritedTextAttribute(self, xmlPath, attrName) -> typing.Union[str, None]:
        """Find the "youngest" parent - or self that has the required attribute and return the attribute value
           If none of the parent elements has the required attribute, return None
        """
        path = self.findInheritedAttribute(xmlPath, attrName)

        if path:
            return self.getTextAttribute(path, attrName)
        return None

    #
    def clearComments(self):
        """Remove all comment nodes from tixi"""
        cmt = "//comment()"
        for path in self.xPathExpressionGetAllXPaths(cmt):
            self.removeElement(path)
