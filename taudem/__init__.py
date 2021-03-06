# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TauDEM
                                 A QGIS plugin
 Implementation of TauDEM algorithms within QGIS3.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        Date                 : July 2018
        Copyright            : (C) 2018 by Greg Leonard
        Email                : greg.h.leonard@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Greg Leonard'
__date__ = 'July 2018'
__copyright__ = '(C) 2018 by Greg Leonard'


def classFactory(iface):  

    from .TauDEMAlgorithmPlugin import TauDEMAlgorithmPlugin
    return TauDEMAlgorithmPlugin(iface)
