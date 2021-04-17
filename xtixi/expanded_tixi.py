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

import re
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

    #
    def getUnknownNSelementPath(self, path, processed_path=None, elements=None):
        """ Carve the way down to an element, without knowing the namespace URI or having the namespace
        registered/declared.
        Comment elements are ignored and do not influence the index
        This is a recursive function
        :return: xPath in the form "/*[3]/*[1]/*[1]/*[2]
        """
        if elements is None:
            if "/" not in path:
                raise Tixi3Exception(ReturnCode.INVALID_XPATH, path)
            # The first element would be an empty string, as the path starts with "/"
            elements = path.split("/")[1:]


        elif elements == []:
            # previous recursion has already found the right element
            return processed_path
        if processed_path is None:
            processed_path = "/"

        nextChild = elements[0]
        nextChildName = ExpandedTixi.elementName("/" + nextChild)
        nextChildNumber = ExpandedTixi.elementNumber("/" + nextChild)

        # For non-unique names, need to loop through all children to make sure the count is equal 1
        isNameUnique = nextChildName != nextChild

        childOccurrences = 0
        commentsFound = 0
        elementFound = False
        for i in range(1, self.getNumberOfChilds(processed_path) + 1):
            childName = self.getChildNodeName(processed_path, i)
            if childName == "#comment":
                commentsFound += 1
            if childName != nextChildName:
                continue

            childOccurrences += 1

            elementFound = True
            I = i - commentsFound

            if not isNameUnique and childOccurrences > 1:
                raise Tixi3Exception(ReturnCode.ELEMENT_PATH_NOT_UNIQUE, path)

            if isNameUnique and childOccurrences == nextChildNumber:
                break

        if not elementFound or childOccurrences != nextChildNumber:
            raise Tixi3Exception(ReturnCode.ELEMENT_NOT_FOUND, path)

        if processed_path == "/":
            processed_path = ""
        processed_path = "{}/*[{}]".format(processed_path, I)
        return self.getUnknownNSelementPath(path, processed_path, elements[1:])

    #
    def getURI(self, path):
        """
        Get URI of the element in path.
        :param path: Path to the element of interest
        :return: None, or a tuple of:
                - path to the ancestor (or self) of the element, on which the youngest URI is defined.
                - URI string
        """

        # First, create a working copy of own XML structure
        tmp_tixi = ExpandedTixi()
        tmp_tixi.openString(re.sub("\s+<", "<", self.exportDocumentAsString()))
        tmp_tixi.clearComments()
        path_local = tmp_tixi.getUnknownNSelementPath(path)

        # Now, on that copy, remove all elements that do not belong to the element branch
        elem_chain = path_local.split("/")[1:]
        chain_path = "/"
        for i in range(len(elem_chain)):
            # This path doesn't matter - it's the number that does
            next_elem = "/" + elem_chain[i]
            num = ExpandedTixi.elementNumber(next_elem)
            for j in range(1, tmp_tixi.getNumberOfChilds(chain_path) + 1):
                if j < num:
                    tmp_tixi.removeElement(chain_path + "/*[1]")
                elif j == num:
                    # This element is a part of the path. Do nothing
                    pass
                elif j > num:
                    tmp_tixi.removeElement(chain_path + "/*[2]")
            if chain_path == "/":
                chain_path = ""
            chain_path += "/*[1]"

        # And now get rid of all children of the element
        for j in range(1, tmp_tixi.getNumberOfChilds(chain_path) + 1):
            tmp_tixi.removeElement(chain_path + "/*[1]")

        # Now we should only have a cascade of single nodes. Get the list of opening tags
        xml_tags = re.findall(r"<[^/\?]\S+.*?[^\?]>", tmp_tixi.exportDocumentAsString())

        elements = path.split("/")
        assert len(xml_tags) == len(elements[1:])

        # Look for an xmlns attribute (looking backwards, will yield the youngest one first)
        xmlns = re.compile(r'xmlns=[\'\"](\S+)[\'\"]')
        for tag in reversed(xml_tags):
            m = xmlns.search(tag)
            if not m:
                xml_tags.pop(-1)
                continue
            uri = m.groups(0)[0]
            path_out = "/".join(elements[:len(xml_tags) + 1])
            return path_out, uri
        return None, None

    #
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

        xpath = "{}/ancestor-or-self::*[@{}]".format(xmlPath, attrName)
        try:

            return self.xPathExpressionGetXPath(xpath, self.xPathEvaluateNodeNumber(xpath))
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
        for path in reversed(self.xPathExpressionGetAllXPaths(cmt)):
            self.removeElement(path)
