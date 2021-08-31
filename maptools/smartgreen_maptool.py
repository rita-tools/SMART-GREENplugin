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

from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QCursor

from qgis.gui import (
    QgsMapTool
)


class SmartGreenMapTool(QgsMapTool):
    """
    Base class for all the map tools
    """

    highLightedPoints = []
    
    def __init__(self, iface, button):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.msg_bar = iface.mainWindow().statusBar()
        self.cursor = QCursor(Qt.CrossCursor)
        self.button = button
        

        settings = QSettings()

    def activate(self):
        """
        Gets called when the tool is activated
        """
        QgsMapTool.activate(self)
        self.canvas.setCursor(self.cursor)
        self.button.setChecked(True)

    def deactivate(self):
        """
        Gets called whenever the tool is deactivated directly or indirectly
        """
        QgsMapTool.deactivate(self)
        self.button.setChecked(False)

    # pylint: disable=no-self-use
    def isZoomTool(self):
        """
        Will return if this is a zoom tool
        """
        return False

    def setCursor(self, cursor):
        """
        Set the cursor for this maptool
        """
        self.cursor = QCursor(cursor)

    # ===========================================================================
    # Events
    # ===========================================================================

    def canvasReleaseEvent(self, event):
        """
        Issues rightClicked and leftClicked events
        """
        eb = event.button()
        print('Qt.RightButton:', Qt.RightButton)
        if eb == Qt.RightButton:
            self.rightClicked(event)
        else:
            self.leftClicked(event)

    def canvasDoubleClickEvent(self, event):
        """
        Forwards to doubleClicked
        """
        try:
            self.doubleClicked(event)
        except AttributeError:
            pass
