# -*- coding: utf-8 -*-

"""
***************************************************************************
    TauDEMUtils.py
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
import subprocess
import getpass
from sys import platform
if platform=='linux' or platform=='darwin':
    import pwd
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsApplication,QgsMessageLog
from qgis.core import Qgis
from processing.core.ProcessingConfig import ProcessingConfig
#from processing.core.ProcessingLog import ProcessingLog

class TauDEMUtils:

    TAUDEM_FOLDER = 'TAUDEM_FOLDER'
    TAUDEM_MULTIFILE_FOLDER = 'TAUDEM_MULTIFILE_FOLDER'
    MPIEXEC_FOLDER = 'MPIEXEC_FOLDER'
    MPI_PROCESSES = 'MPI_PROCESSES'

    @staticmethod
    def taudemPath():
        folder = ProcessingConfig.getSetting(TauDEMUtils.TAUDEM_FOLDER)
        if folder is None:
            folder = ''

            if  platform=='linux' or platform=='darwin':
                testfolder = '/usr/local/taudem'
                if os.path.exists(os.path.join(testfolder, 'slopearea')):
                    folder = testfolder
                else:
                    testfolder = '/usr/local/bin'
                    if os.path.exists(os.path.join(testfolder, 'slopearea')):
                        folder = testfolder
            if platform=='win32':
                testfolder = 'C:/taudem'
                if os.path.exists(os.path.join(testfolder, 'slopearea')):
                    folder = testfolder
        return folder

    @staticmethod
    def mpiexecPath():
        folder = ProcessingConfig.getSetting(TauDEMUtils.MPIEXEC_FOLDER)
        if folder is None:
            folder = ''

        if platform=='linux' or platform=='darwin':
            testfolder = '/usr/local/bin/'
            if os.path.exists(os.path.join(testfolder, 'mpiexec')):
                folder = testfolder
        if platform=='win32':
            testfolder = 'C:/Program Files/Microsoft MPI/Bin'
            if os.path.exists(os.path.join(testfolder, 'mpiexec.exe')):
                folder = testfolder
        return folder

    @staticmethod
    def taudemDescriptionPath():
        return os.path.normpath(
            os.path.join(os.path.dirname(__file__), 'description'))

    @staticmethod
    def executeTauDEM(command, feedback):
        loglines = []
        loglines.append(TauDEMUtils.tr('TauDEM execution console output'))
        fused_command=TauDEMUtils.escapeAndJoin(command)
        feedback.pushInfo(TauDEMUtils.tr('TauDEM command:'))
        feedback.pushCommandInfo(fused_command.replace('" "', ' ').strip('"'))
        def demote(user_uid, user_gid):
            def result():
                os.setgid(user_gid)
                os.setuid(user_uid)
            return result
        if platform=='linux' or platform=='darwin':
            user_name=getpass.getuser()
            pw_record = pwd.getpwnam(user_name)
            user_name      = pw_record.pw_name
            user_home_dir  = pw_record.pw_dir
            user_uid       = pw_record.pw_uid
            user_gid       = pw_record.pw_gid
            env = os.environ.copy()
            cwd=ProcessingConfig.getSetting(ProcessingConfig.OUTPUT_FOLDER)
            env[ 'HOME'     ]  = user_home_dir
            env[ 'PWD'      ]  = cwd
            env[ 'LOGNAME'  ]  = user_name
            env[ 'USER'     ]  = user_name
            proc = subprocess.Popen(
                fused_command,
                shell=True,
                preexec_fn=demote(user_uid, user_gid),
                env=env,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stdin=open(os.devnull),
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                ).stdout
        elif platform=='win32':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            proc = subprocess.Popen(
                fused_command,
                stdout=subprocess.PIPE,
                shell=True,
                stdin=open(os.devnull),
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                startupinfo=si
                ).stdout
        for line in iter(proc.readline, ''):
            feedback.pushConsoleInfo(line)
            loglines.append(line)
        QgsMessageLog.logMessage('\n'.join(loglines),level=Qgis.Info)

    @staticmethod
    def tr(string, context=''):
        if context == '':
            context = 'TauDEMUtils'
        return QCoreApplication.translate(context, string)

    @staticmethod
    def escapeAndJoin(strList):
        joined = ''
        for s in strList:
            if s[0] != '-' and ' ' in s:
                escaped = '"' + s.replace('\\', '\\\\').replace('"', '\\"') \
                    + '"'
            else:
                escaped = s
            joined += escaped+' '
        return joined.strip()
