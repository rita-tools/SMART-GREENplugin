# -*- coding: utf-8 -*-

"""
/***************************************************************************
 SMARTGREEN
 A QGIS plugin to support water managers in the process
 of building and simulating different land uses scenarios and LIDs planning.
 -------------------
		begin				: 2017-04-21
		copyright			: (C) 2017 by UNIMI
		email				: enrico.chiaradia@unimi.it
 ***************************************************************************/

/***************************************************************************
 *																		 *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or	 *
 *   (at your option) any later version.								   *
 *																		 *
 ***************************************************************************/
"""

__author__ = 'UNIMI'
__date__ = '2017-04-21'
__copyright__ = '(C) 2017 by UNIMI'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import sys
import inspect

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load MobidicUI class from file MobidicUI.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

    if cmd_folder not in sys.path:
        sys.path.insert(0, cmd_folder)

    from .smartgreen_plugin import SmartGreenPlugin
    return SmartGreenPlugin(iface)
