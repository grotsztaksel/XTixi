# -*- coding: utf-8 -*-
"""
Created on Sat Nov 14 17:57:28 2020

@author: Piotr Gradkowski <grotsztaksel@o2.pl>
"""

__authors__ = ['Piotr Gradkowski <grotsztaksel@o2.pl>']
__date__ = '2020-11-14'
__all__ = ['Tixi', 'TixiException', 'ReturnCode']

try:
    # If Tixi path is specified in PYTHONPATH
    from tixi3wrapper import ReturnCode
    from tixi3wrapper import Tixi3Exception as TixiException
except ImportError:
    # This usually works in Anaconda environment
    from tixi3.tixi3wrapper import ReturnCode
    from tixi3.tixi3wrapper import Tixi3Exception as TixiException

from .expanded_tixi import ExpandedTixi as Tixi
