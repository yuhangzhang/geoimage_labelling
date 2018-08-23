#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from skimage.draw import polygon

import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore

import cv2
from cv2 import imwrite as imwrite

import numpy as np
import shapefile as sf

class InteractiveDialog(QDialog):

    def __init__(self, parent=None):
        super(QDialog, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.le = QLineEdit()
        self.le.setValidator(QIntValidator())
        self.le.setMaxLength(2)
        self.le.setAlignment(Qt.AlignRight)
        self.le.setFont(QFont("Arial", 20))

        layout.addWidget(self.le)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)



    @staticmethod
    def gettext():
        dialog = InteractiveDialog()
        result = dialog.exec_()
        return(dialog.le.text(),result==QDialog.Accepted)



class InteractiveGraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super(InteractiveGraphicsScene, self).__init__(parent)

        #initiate input image
        self.pixmap = QPixmap('Desert.jpg')

        #initiate label image
        self.label_all = np.zeros([self.pixmap.height(), self.pixmap.width()])
        self.label_all.fill(Qt.black)


        self.draw_switch = False

        self.dialog = InteractiveDialog()

        self.poly = []



    def mousePressEvent(self, event):
        super(InteractiveGraphicsScene, self).mousePressEvent(event)

        #prepare for a new crop
        if event.button() == QtCore.Qt.LeftButton:
            self.draw_switch = True
            self.lastx = event.pos().x()
            self.lasty = event.pos().y()
            self.polyx = []
            self.polyy = []
            self.path = []

    def mouseReleaseEvent(self, event):
        super(InteractiveGraphicsScene, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.draw_switch = False

            # finish the current crop
            if event.button() == QtCore.Qt.LeftButton:
                label = self.dialog.gettext()

                print(label)

                if label[1]==True:
                    self.cleancontour()

                    poly = QPolygon()

                    for i in range(len(self.polyx)):
                        poly.append(QPoint(self.polyx[i], self.polyy[i]))

                    brush = QBrush()
                    brush.setColor(Qt.white)
                    brush.setStyle(Qt.Dense4Pattern)
                    self.addPolygon(QPolygonF(poly),brush=brush)




                for p in self.path:
                    self.removeItem(p)












    def mouseMoveEvent(self, event):
        super(InteractiveGraphicsScene, self).mousePressEvent(event)

        #collect all points mouse moved through
        if self.draw_switch == True:
            x = event.scenePos().x()
            y = event.scenePos().y()

            #show trace on the screen
            path = QtGui.QPainterPath()
            path.setFillRule(QtCore.Qt.WindingFill)
            path.moveTo(self.lastx, self.lasty)
            path.lineTo(x, y)

            self.path.append(self.addPath(path))

            #keep vertex for label generation later
            if x<self.pixmap.width() and y<self.pixmap.height():
                self.polyx.append(x)
                self.polyy.append(y)

            #update lastx lasty
            self.lastx = x
            self.lasty = y


    def addPixmap(self):
        super(InteractiveGraphicsScene, self).addPixmap(self.pixmap)


    def cleancontour(self):
        i,j = polygon(self.polyx,self.polyy)
        self.label_all[j,i]=255
        imwrite('c.png',self.label_all)



class myshapefile:
    def __init__(self):
        self.inputfile = sf.Reader("/g/data1a/ge3/AEM_Model/3D_AEM_model_V3.shp")
        self.inputrecord = self.inputfile.records()










class TestWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.scene = InteractiveGraphicsScene()
        self.scene.addItem(QGraphicsPixmapItem())
        self.view = QGraphicsView(self.scene)

        self.button = QPushButton("load image")
        self.button.clicked.connect(self.do_test)

        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.view)
        self.setLayout(layout)

    def do_test(self):

        self.scene.addPixmap()
        #self.view.fitInView(QRectF(0, 0, self.img.size().width(), self.img.size().height()), Qt.KeepAspectRatio)
        #self.scene.update()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = TestWidget()
    widget.resize(640, 480)
    widget.show()

    sys.exit(app.exec_())