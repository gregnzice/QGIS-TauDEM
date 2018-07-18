# -*- coding: utf-8 -*-

"""
***************************************************************************
    TauDEMAlgorithm.py
    ---------------------
    Date                 : July 2018
    Copyright            : (C) 2018 by Greg Leonard
    Email                : greg.h.leonard@gmail.com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Greg Leonard'
__date__ = 'July 2018'
__copyright__ = '(C) 2018, Greg Leonard'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
from ast import literal_eval
from distutils.util import strtobool
from processing.core.ProcessingLog import ProcessingLog
from processing.core.ProcessingConfig import ProcessingConfig, Setting
from PyQt5.QtCore import QCoreApplication, QUrl
from PyQt5.QtGui import QIcon
from qgis.core import (QgsProcessing,
                       QgsMessageLog,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingException,
                       QgsProcessingUtils,
                       QgsProcessingContext,
                       QgsProcessingParameterString,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFileDestination,
                       QgsDefaultValue,
                       QgsRasterLayer,
                       QgsVectorLayer,
                       QgsProcessingParameterFeatureSink,
                       Qgis)

from processing.core.parameters import getParameterFromString
from processing.core.outputs import getOutputFromString
from .TauDEMUtils import TauDEMUtils

class TauDEMAlgorithm(QgsProcessingAlgorithm):

    STAT_DICT = {0: 'min', 1: 'max', 2: 'ave'}
    DIST_DICT = {
        0: 'p',
        1: 'h',
        2: 'v',
        3: 's',
    }

    def __init__(self, descriptionfile):
        QgsProcessingAlgorithm.__init__(self)
        self.descriptionFile = descriptionfile
        self.defineCharacteristicsFromFile()

    def copy(self):
        newone = TauDEMAlgorithm(self.descriptionFile)
        newone.provider = self.provider
        return newone

    def icon(self):
        return QIcon(":/plugins/taudem/taudem.svg")
    def displayName(self):
        return self.displayname
    def name(self):
        return self.cmdName
    def group(self):
        return self.groupid
    def groupId(self):
        return self.groupid

    def initAlgorithm(self, config):
        for par in self.param:
            pl=par.split('|')
            if pl[0]=='ParameterRaster':
                self.addParameter(QgsProcessingParameterRasterLayer(pl[1],self.tr(pl[2]),'',bool(strtobool(pl[3]))))
            if pl[0]=='ParameterVector':
                self.addParameter(QgsProcessingParameterVectorLayer(pl[1],self.tr(pl[2]),[QgsProcessing.TypeVector],'',bool(strtobool(pl[3]))))
            if pl[0]=='ParameterNumber':
                try:
                    int(pl[5])
                    if pl[4] !='None':
                        self.addParameter(QgsProcessingParameterNumber(pl[1],self.tr(pl[2]),0,int(pl[5]),False,int(pl[3]),int(pl[4])))
                    else:
                        self.addParameter(QgsProcessingParameterNumber(pl[1],self.tr(pl[2]),0,int(pl[5]),False,int(pl[3])))
                except ValueError:
                    if pl[4] !='None':
                        self.addParameter(QgsProcessingParameterNumber(pl[1],self.tr(pl[2]),1,float(pl[5]),False,float(pl[3]),float(pl[4])))
                    else:
                        self.addParameter(QgsProcessingParameterNumber(pl[1],self.tr(pl[2]),1,float(pl[5]),False,float(pl[3])))
            if pl[0]=='ParameterBoolean':
                self.addParameter(QgsProcessingParameterBoolean(pl[1],self.tr(pl[2]),bool(strtobool(pl[3])),False))
            if pl[0]=='ParameterEnum':
                self.addParameter(QgsProcessingParameterEnum(pl[1],self.tr(pl[2]),literal_eval(pl[3]),False,pl[4],False))
        for out in self.outputline:
            ol=out.split('|')
            if ol[0]=='OutputRaster':
                self.addParameter(QgsProcessingParameterRasterDestination(ol[1][1:],self.tr(ol[2])))
            if ol[0]=='OutputFile':
                self.addParameter(QgsProcessingParameterFileDestination(ol[1][1:],self.tr(ol[2])))

    def defineCharacteristicsFromFile(self):
        self.param=[]
        self.outputline=[]

        lines = open(self.descriptionFile)
        self.displayname = lines.readline().strip('\n').strip()
        self.cmdName = lines.readline().strip('\n').strip()
        self.groupid = lines.readline().strip('\n').strip()

        line = lines.readline().strip('\n').strip()

        while line != '':
            try:
                line = line.strip('\n').strip()
                if line.startswith('Parameter'):
                    self.param.append(line)
                else:
                    self.outputline.append(line)
                line = lines.readline().strip('\n').strip()
            except Exception as e:
                QgsMessageLog.logMessage(self.tr('Could not load TauDEM algorithm: %s\n%s' % (self.descriptionFile, line)),Qgis.Critical)
                raise e
        lines.close()
        return

    def processAlgorithm(self, parameters, context, feedback):
        commands = []
        commands.append(os.path.join(TauDEMUtils.mpiexecPath(), 'mpiexec'))

        processNum = int(ProcessingConfig.getSetting(TauDEMUtils.MPI_PROCESSES))
        if processNum <= 0:
            raise QgsProcessingException(
                self.tr('Wrong number of MPI processes used. Please set '
                        'correct number before running TauDEM algorithms.'))

        commands.append('-n')
        commands.append(str(processNum))
        if self.cmdName[-1]=='2':
            commands.append(os.path.join(TauDEMUtils.taudemPath(), self.cmdName)[:-1])
        else:
            commands.append(os.path.join(TauDEMUtils.taudemPath(), self.cmdName))
        self.outdescription=[]
        self.outputdestination=[]
        pflag=0
        mflag=0
        pparametertxt='-par'
        mparametertxt='-m'
        for param in self.parameterDefinitions():
            if isinstance(param, QgsProcessingParameterNumber):
                if param.name()[:4]=='-par':
                    pflag=1
                    pparametertxt=pparametertxt+' '+self.parameterAsString(parameters,param.name(),context)

                elif param.name()=='-thresh':
                    if commands[-2]=='-mask':
                        commands.append(param.name())
                        commands.append(self.parameterAsString(parameters,param.name(),context))
                else:
                    commands.append(param.name())
                    commands.append(self.parameterAsString(parameters,param.name(),context))

            elif isinstance(param, (QgsProcessingParameterRasterLayer)):
                inLayer = self.parameterAsRasterLayer(parameters, param.name(), context)
                if inLayer:
                    commands.append(param.name())
                    commands.append(inLayer.source())
            elif isinstance(param, (QgsProcessingParameterVectorLayer)):
                inLayer=self.parameterAsVectorLayer(parameters, param.name(), context)
                if inLayer:
                    commands.append(param.name())
                    commands.append(inLayer.source())

            elif isinstance(param, QgsProcessingParameterBoolean):
                commands.append(param.name())
            elif isinstance(param, QgsProcessingParameterString):
                commands.append(param.name())
                commands.append(self.parameterAsString(parameters,param.name(),context))
            elif isinstance(param, QgsProcessingParameterEnum):
                if param.name()[:2]=='-m':
                    mflag=1
                    if param.name()[2:4]=='sm':
                        mparametertxt=mparametertxt+' '+str(self.STAT_DICT[self.parameterAsEnum(parameters,
            param.name(),context)])
                    if param.name()[2:4]=='dm':
                        mparametertxt=mparametertxt+' '+str(self.DIST_DICT[self.parameterAsEnum(parameters,
            param.name(),context)])
                if param.name()[:4]=='-par':
                    pflag=1
                    pparametertxt=pparametertxt+' '+str(self.parameterAsEnum(parameters,
        param.name(),context))

            elif isinstance(param, QgsProcessingParameterRasterDestination):
                outLayer = self.parameterAsOutputLayer(parameters, param.name(), context)
                commands.append('-'+param.name())
                commands.append(outLayer)
            elif isinstance(param, QgsProcessingParameterFileDestination):
                outLayer = self.parameterAsOutputLayer(parameters, param.name(), context)
                commands.append('-'+param.name())
                commands.append(outLayer)
        if pflag==1:
            commands.append(pparametertxt)
        if mflag==1:
            commands.append(mparametertxt)
        TauDEMUtils.executeTauDEM(commands, feedback)
        return {}

    def helpUrl(self):
        helpPath='http://hydrology.usu.edu/taudem/taudem5/help53/'
        if self.displayname[-1]=='2':
            helpname=self.displayname[:-1]
        else:
            helpname=self.displayname
        return helpPath + '{}.html'.format(helpname.replace(" ", "").replace("-",""))

    def shortHelpString(self):
        with open(self.descriptionFile) as helpf:
            help=helpf.read()
        return help

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
    def createInstance(self):
        return TauDEMAlgorithm(self.descriptionFile)
