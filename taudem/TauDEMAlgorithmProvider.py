# -*- coding: utf-8 -*-

"""
/***************************************************************************
    TauDEMAlgorithmProvider.py
    ---------------------
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

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'
import os
from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon
from qgis.core import QgsProcessingProvider,QgsMessageLog,Qgis
from processing.core.ProcessingLog import ProcessingLog
from processing.core.ProcessingConfig import ProcessingConfig, Setting
from .TauDEMUtils import TauDEMUtils
from . import resources
from .TauDEMAlgorithm import TauDEMAlgorithm

class TauDEMAlgorithmProvider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)

    def name(self):
        return self.tr('TauDEM')

    def icon(self):
        return QIcon(":/plugins/taudem/taudem.svg")

    def load(self):
        ProcessingConfig.settingIcons[self.name()] = self.icon()
        ProcessingConfig.addSetting(Setting(self.name(), 'ACTIVATE_TauDEM',
                                            self.tr('Activate'), True))
        ProcessingConfig.addSetting(Setting(self.name(),
                                            TauDEMUtils.TAUDEM_FOLDER,
                                            self.tr('TauDEM command line tools folder'),
                                            TauDEMUtils.taudemPath(), valuetype=Setting.FOLDER))
        ProcessingConfig.addSetting(Setting(self.name(),
                                            TauDEMUtils.MPIEXEC_FOLDER,
                                            self.tr('MPICH2/OpenMPI bin directory'),
                                            TauDEMUtils.mpiexecPath(), valuetype=Setting.FOLDER))
        ProcessingConfig.addSetting(Setting(self.name(),
                                            TauDEMUtils.MPI_PROCESSES,
                                            self.tr('Number of MPI parallel processes to use'), 2))
        ProcessingConfig.readSettings()
        self.refreshAlgorithms()
        return True
    def unload(self):
        ProcessingConfig.removeSetting('ACTIVATE_TauDEM')
        ProcessingConfig.removeSetting(TauDEMUtils.TAUDEM_FOLDER)
        ProcessingConfig.removeSetting(TauDEMUtils.MPIEXEC_FOLDER)
        ProcessingConfig.removeSetting(TauDEMUtils.MPI_PROCESSES)

    def isActive(self):
        return ProcessingConfig.getSetting('ACTIVATE_TauDEM')

    def setActive(self, active):
        ProcessingConfig.setSettingValue('ACTIVATE_TauDEM', active)
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
    def loadAlgorithms(self):
        self.algs = []
        basePath = TauDEMUtils.taudemDescriptionPath()
        folder = basePath

        for descriptionFile in os.listdir(folder):
            if descriptionFile.endswith('.txt'):
                descriptionFile = os.path.join(folder, descriptionFile)
                self._algFromDescription(descriptionFile)
        for alg in self.algs:
            self.addAlgorithm (alg)

    def _algFromDescription(self, descriptionFile):
        try:
            alg = TauDEMAlgorithm(descriptionFile)
            if alg.name().strip() != '':
                self.algs.append(alg)
            else:
                QgsMessageLog.logMessage(self.tr('Could not open TauDEM algorithm: %s' % descriptionFile),level=Qgis.Critical)
        except Exception as e:
            QgsMessageLog.logMessage(self.tr('Could not open TauDEM algorithm %s:\n%s' % (descriptionFile, str(e))),level=Qgis.Critical)
            raise e
    def id(self):
        return 'taudem'

    def longName(self):
        return self.name()
