#!/usr/bin/env python
# --!-- coding: utf8 --!--
import re
from PyQt5.QtGui import QFont, QTextCharFormat
from PyQt5.QtWidgets import QPlainTextEdit, qApp, QFrame

from manuskript.exporter.basic import basicFormat
from manuskript.functions import mainWindow
from manuskript.models.outlineModel import outlineItem
from manuskript.ui.exporters.manuskript.plainTextSettings import exporterSettings


class plainText(basicFormat):
    name = qApp.tr("Plain text")
    description = qApp.tr("""Simplest export to plain text. Allows you to use your own markup not understood
                  by manuskript, for example <a href='www.fountain.io'>Fountain</a>.""")
    implemented = True
    requires = {
        "Settings": True,
        "Preview": True,
    }

    @classmethod
    def settingsWidget(cls):
        w = exporterSettings(cls)
        w.loadSettings()
        return w

    @classmethod
    def previewWidget(cls):
        w = QPlainTextEdit()
        w.setFrameShape(QFrame.NoFrame)
        w.setReadOnly(True)
        return w

    @classmethod
    def output(cls, settings):
        return cls.concatenate(mainWindow().mdlOutline.rootItem, settings)

    @classmethod
    def preview(cls, settingsWidget, previewWidget):
        settings = settingsWidget.getSettings()

        # Save settings
        settingsWidget.writeSettings()

        r = cls.output(settings)

        # Set preview font
        cls.preparesTextEditView(previewWidget, settings["Preview"]["PreviewFont"])

        previewWidget.setPlainText(r)

    @classmethod
    def preparesTextEditView(cls, view, textFont):
        cf = QTextCharFormat()
        f = QFont()
        f.fromString(textFont)
        cf.setFont(f)
        view.setCurrentCharFormat(cf)

    @classmethod
    def concatenate(cls, item: outlineItem, settings) -> str:
        s = settings
        r = ""

        # Do we include item
        if not item.compile() or s["Content"]["IgnoreCompile"]:
            return ""

        # What do we include
        l = item.level()
        if l >= 0:  # item is not root

            if item.isFolder():
                if not s["Content"]["More"] and s["Content"]["FolderTitle"] or\
                       s["Content"]["More"] and s["Content"]["FolderTitle"][l]:

                    r += cls.processTitle(item.title(), l, settings)

            elif item.isText():
                if not s["Content"]["More"] and s["Content"]["TextTitle"] or \
                       s["Content"]["More"] and s["Content"]["TextTitle"][l]:

                    r += cls.processTitle(item.title(), l, settings)

                if not s["Content"]["More"] and s["Content"]["TextText"] or \
                       s["Content"]["More"] and s["Content"]["TextText"][l]:

                    r += cls.processText(item.text(), settings)

        content = ""

        # Add item children
        last = None
        for c in item.children():

            # Separator
            if last:
                # Between folder
                if last == c.type() == "folder":
                    content += s["Separator"]["FF"]

                elif last == c.type() == "md":
                    content += s["Separator"]["TT"]

                elif last == "folder" and c.type() == "md":
                    content += s["Separator"]["FT"]

                elif last == "md" and c.type() == "folder":
                    content += s["Separator"]["TF"]

            content += cls.concatenate(c, settings)

            last = c.type()

        # r += cls.processContent(content, settings)
        r += content

        return r

    @classmethod
    def processTitle(cls, text, level, settings):
        return text + "\n"

    @classmethod
    def processText(cls, content, settings):
        s = settings["Transform"]

        if s["Dash"]:
            content = content.replace("---", "—")

        if s["Ellipse"]:
            content = content.replace("...", "…")

        if s["Spaces"]:
            o = ""
            while o != content:
                o = content
                content = content.replace("  ", " ")

        if s["DoubleQuotes"]:
            q = s["DoubleQuotes"].split("___")
            s["Custom"].append([True, '"(.*?)"', "{}\\1{}".format(q[0], q[1]), True])

        if s["SingleQuote"]:
            q = s["SingleQuote"].split("___")
            s["Custom"].append([True, "'(.*?)'", "{}\\1{}".format(q[0], q[1]), True])

        for enabled, A, B, reg in s["Custom"]:
            if not enabled:
                continue

            if not reg:
                content = content.replace(A, B)

            else:
                content = re.sub(A, B, content)

        content += "\n"

        return content

