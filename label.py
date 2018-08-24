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
import sklearn.decomposition as sd

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
        self.shapefile = myshapefile()
        arr = self.shapefile.getimage(1600, 600)
        qimg = QImage(arr,arr.shape[1],arr.shape[0],QImage.Format_RGB888)
        self.pixmap = QPixmap(qimg)

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
                self.currentlabel = self.dialog.gettext()

                print(self.currentlabel)

                if self.currentlabel[1]==True:
                    self.cleancontour()

                    poly = QPolygon()

                    for i in range(len(self.polyx)):
                        poly.append(QPoint(self.polyx[i], self.polyy[i]))

                    brush = QBrush()
                    brush.setColor(Qt.white)
                    brush.setStyle(Qt.Dense6Pattern)
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
        self.label_all[j,i]=int(self.currentlabel[0])
        imwrite('c.png',self.label_all)

    def export(self):
        fw = open('exported_labels.txt', 'w')

        for h in range(self.label_all.shape[0]):
            for w in range(self.label_all.shape[1]):
                if self.label_all[h,w]>0:
                    points = self.shapefile.getpoint(w,h)

                    for p in points:
                        np.savetxt(fw, np.append(p,self.label_all[h,w]).reshape(1, -1), fmt='%s')

        fw.close()



class myshapefile:
    def __init__(self):
        inputfile = sf.Reader("/g/data1a/ge3/AEM_Model/3D_AEM_model_V3.shp")
        inputrecord = np.array(inputfile.records())

        xyz = inputrecord[:,10:13].astype(float) #nx3 matrix

        height = len(np.unique(xyz[:,2], axis=0))
        width = len(np.unique(xyz[:,0:2], axis=0))

        #project x, y onto a line
        pca = sd.PCA(n_components=1)
        pca.fit(xyz[:,0:2])
        xy = pca.transform(xyz[:,0:2])

        print(inputrecord.shape)
        print(xy.shape)


        self.point = np.hstack([inputrecord,xy.reshape(-1,1),inputrecord[:,12].reshape(-1,1)])



    def getpoint(self,w,h):
        return self.bucket[w][h]

    def getimage(self,width,height):
        img = np.zeros([height,width,3],dtype=float)

        self.bucket = [[[] for h in range(height)] for w in range(width)]

        self.point[:,-1] = np.round(
                                    (self.point[:,-1].astype(float) - self.point[:,-1].astype(float).min())
                                    /(self.point[:,-1].astype(float).max() - self.point[:,-1].astype(float).min())
                                    *(height-1)
                                   )
        self.point[:,-2] = np.round(
                                    (self.point[:,-2].astype(float) - self.point[:,-2].astype(float).min())
                                    /(self.point[:, -2].astype(float).max() - self.point[:, -2].astype(float).min())
                                    *(width-1)
                                   )

        bucket_size = np.zeros([height,width,3],dtype=np.int)

        for p in self.point:
            if p[1]!='Surface':
                #p = p[[2,4,5,-2,-1]].astype(float)
                #p = p[[2, 2, 2, -2, -1]].astype(float)

                p[-1]=height-p[-1]-1

                self.bucket[int(p[-2])][int(p[-1])].append(p)
                img[int(p[-1]), int(p[-2]), 0] = img[int(p[-1]), int(p[-2]), 0]+p[2]
                img[int(p[-1]), int(p[-2]), 1] = img[int(p[-1]), int(p[-2]), 1]+p[4]
                img[int(p[-1]), int(p[-2]), 2] = img[int(p[-1]), int(p[-2]), 2]+p[5]
                bucket_size[int(p[-1]), int(p[-2]), :] = bucket_size[int(p[-1]), int(p[-2]), :]+1

        for i in range(bucket_size.shape[0]):
            for j in range(bucket_size.shape[1]):
                for k in range(bucket_size.shape[2]):
                    if bucket_size[i,j,k]==0:
                        bucket_size[i, j, k]=1

        img = img/bucket_size

        minr = img[:, :, 0][np.nonzero(img[:, :, 0])].min()
        ming = img[:, :, 1][np.nonzero(img[:, :, 0])].min()
        minb = img[:, :, 2][np.nonzero(img[:, :, 0])].min()

        maxr = img[:, :, 0].max()
        maxg = img[:, :, 1].max()
        maxb = img[:, :, 2].max()

        img[:, :, 0][np.nonzero(img[:, :, 0])] = img[:, :, 0][np.nonzero(img[:, :, 0])] + (maxr - minr)*0.25
        img[:, :, 1][np.nonzero(img[:, :, 1])] = img[:, :, 1][np.nonzero(img[:, :, 1])] + (maxg - ming)*0.25
        img[:, :, 2][np.nonzero(img[:, :, 2])] = img[:, :, 2][np.nonzero(img[:, :, 2])] + (maxb - minb)*0.25

        print(minr, ming, minb)
        print(maxr, maxg, maxb)

        updis = np.zeros([height,width],dtype=np.int)
        img_interpolate = np.zeros([height,width,3],dtype=np.float32)

        for w in range(img.shape[1]):
            dis=0
            lastpoint = img[0,w,:]
            for h in range(img.shape[0]):
                if abs(img[h,w,0])+abs(img[h,w,1])+abs(img[h,w,2])==0:
                    dis=dis+1
                    img_interpolate[h,w,:] = lastpoint
                    updis[h,w] = dis
                else:
                    img_interpolate[h, w, :] = img[h, w, :]
                    dis=0
                    lastpoint = img[h, w, :]

        for w in range(img.shape[1]):
            dis=0
            lastpoint = img[-1,w,:]
            for h in reversed(range(img.shape[0])):
                if abs(img[h,w,0])+abs(img[h,w,1])+abs(img[h,w,2])==0 and abs(img_interpolate[h,w,0])+abs(img_interpolate[h,w,1])+abs(img_interpolate[h,w,2])>0:
                    if abs(lastpoint[0])+abs(lastpoint[1])+abs(lastpoint[2])==0:
                        img_interpolate[h, w, :] = lastpoint
                    else:
                        img_interpolate[h,w,:] = (img_interpolate[h,w,:]*dis+lastpoint*updis[h,w])/(dis+updis[h,w])
                    dis = dis + 1
                elif abs(img[h,w,0])+abs(img[h,w,1])+abs(img[h,w,2])==0:
                    break
                else:
                    dis=0
                    lastpoint = img[h, w, :]

        img_interpolate[:, :, 0] = (img_interpolate[:, :, 0]) * 255 / (maxr + (maxr - minr)*0.25)
        img_interpolate[:, :, 1] = (img_interpolate[:, :, 1]) * 255 / (maxg + (maxg - ming)*0.25)
        img_interpolate[:, :, 2] = (img_interpolate[:, :, 2]) * 255 / (maxb + (maxb - minb)*0.25)




        return(img_interpolate.astype(np.uint8))




class TestWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.scene = InteractiveGraphicsScene()
        self.scene.addItem(QGraphicsPixmapItem())
        self.view = QGraphicsView(self.scene)

        self.button = QPushButton("load image")
        self.button.clicked.connect(self.do_test)

        self.exportbutton = QPushButton("export label")
        self.exportbutton.clicked.connect(self.scene.export)

        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.view)
        layout.addWidget(self.exportbutton)
        self.setLayout(layout)

    def do_test(self):

        self.scene.addPixmap()
        #self.view.fitInView(QRectF(0, 0, self.img.size().width(), self.img.size().height()), Qt.KeepAspectRatio)
        #self.scene.update()



if __name__ == "__main__":

#    x=myshapefile()
#    y=x.getimage(1600,600)
#    cv2.imwrite('gui.png',y)

    app = QApplication(sys.argv)
    widget = TestWidget()
    widget.resize(640, 480)
    widget.show()

    sys.exit(app.exec_())