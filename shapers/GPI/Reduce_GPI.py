# Copyright (c) 2014, Dignity Health
#
#     The GPI core node library is licensed under
# either the BSD 3-clause or the LGPL v. 3.
#
#     Under either license, the following additional term applies:
#
#         NO CLINICAL USE.  THE SOFTWARE IS NOT INTENDED FOR COMMERCIAL
# PURPOSES AND SHOULD BE USED ONLY FOR NON-COMMERCIAL RESEARCH PURPOSES.  THE
# SOFTWARE MAY NOT IN ANY EVENT BE USED FOR ANY CLINICAL OR DIAGNOSTIC
# PURPOSES.  YOU ACKNOWLEDGE AND AGREE THAT THE SOFTWARE IS NOT INTENDED FOR
# USE IN ANY HIGH RISK OR STRICT LIABILITY ACTIVITY, INCLUDING BUT NOT LIMITED
# TO LIFE SUPPORT OR EMERGENCY MEDICAL OPERATIONS OR USES.  LICENSOR MAKES NO
# WARRANTY AND HAS NOR LIABILITY ARISING FROM ANY USE OF THE SOFTWARE IN ANY
# HIGH RISK OR STRICT LIABILITY ACTIVITIES.
#
#     If you elect to license the GPI core node library under the LGPL the
# following applies:
#
#         This file is part of the GPI core node library.
#
#         The GPI core node library is free software: you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version. GPI core node library is distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
#
#         You should have received a copy of the GNU Lesser General Public
# License along with the GPI core node library. If not, see
# <http://www.gnu.org/licenses/>.


# Author: Nick Zwart
# Date: 2012sep02

import gpi
from gpi import QtWidgets

# WIDGET


class ReduceSliders(gpi.GenericWidgetGroup):
    """Combines the BasicCWFCSliders with ExclusivePushButtons
    for a unique widget element useful for reduce dimensions.
    """
    valueChanged = gpi.Signal()

    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.sl = gpi.BasicCWFCSliders()
        self.sl.valueChanged.connect(self.valueChanged)
        # at least one button
        self.button_names = ['C/W', 'B/E', 'Slice', 'Pass']
        self.buttons = []
        cnt = 0
        wdgLayout = QtWidgets.QGridLayout()
        for name in self.button_names:
            newbutton = QtWidgets.QPushButton(name)
            newbutton.setCheckable(True)
            newbutton.setAutoExclusive(True)
            self.buttons.append(newbutton)
            newbutton.clicked.connect(self.findValue)
            newbutton.clicked.connect(self.valueChanged)
            wdgLayout.addWidget(newbutton, 0, cnt, 1, 1)
            cnt += 1
        # layout
        wdgLayout.addWidget(self.sl, 1, 0, 1, 4)
        wdgLayout.setVerticalSpacing(0)
        wdgLayout.setSpacing(0)
        self.setLayout(wdgLayout)
        # default
        self.set_min(1)
        self._selection = 3  # pass is default
        self.buttons[self._selection].setChecked(True)
        self.sl.set_allvisible(False)

    # setters
    def set_val(self, val):
        """A python-dict containing keys: center, width, floor, ceiling,
        and selection.
        """
        if 'center' in val:
            self.sl.set_center(val['center'])
        if 'width' in val:
            self.sl.set_width(val['width'])
        if 'floor' in val:
            self.sl.set_floor(val['floor'])
        if 'ceiling' in val:
            self.sl.set_ceiling(val['ceiling'])
        if 'selection' in val:
            self._selection = val['selection']
        self.buttons[self._selection].blockSignals(True)
        self.buttons[self._selection].setChecked(True)
        self.buttons[self._selection].blockSignals(False)
        self.findValue(None)

    def set_min(self, val):
        """A min value for center, width, floor and ceiling (int)."""
        self.sl.set_min(val)

    def set_max(self, val):
        """A max value for center, width, floor and ceiling (int)."""
        self.sl.set_max(val)

    def set_quietmax(self, val):
        if val is not None:
            self.blockSignals(True)
            self.set_max(val)
            self.blockSignals(False)

    # getters
    def get_val(self):
        val = {}
        val['selection'] = self._selection
        val['center'] = self.sl.get_center()
        val['width'] = self.sl.get_width()
        val['floor'] = self.sl.get_floor()
        val['ceiling'] = self.sl.get_ceiling()
        return val

    def get_min(self):
        return self.sl.get_min()

    def get_max(self):
        return self.sl.get_max()

    def get_quietmax(self):
        # don't return a value so that network deserialize passes 'None' to
        # the setter
        pass

    # support

    def setCropBounds(self):
        self.sl.set_min_width(1)

    def setSliceBounds(self):
        self.sl.set_min_width(0)
        self.sl.set_width(1)

    def setPassBounds(self):
        self.sl.set_min_width(1)
        self.sl.set_width(self.get_max())
        # JGP For Pass, reset cwfc
        self.sl.set_center((self.get_max()+1)//2)
        self.sl.set_width(self.get_max())
        self.sl.set_floor(1)
        self.sl.set_ceiling(self.get_max())

    def findValue(self, value):
        cnt = 0
        for button in self.buttons:
            if button.isChecked():
                self._selection = cnt
            cnt += 1
        # hide appropriate sliders
        if self._selection == 0:  # C/W
            self.sl.set_cwvisible(True)
            self.setCropBounds()
        elif self._selection == 1:  # B/E
            self.sl.set_fcvisible(True)
            self.setCropBounds()
        elif self._selection == 2:  # slice
            self.sl.set_slicevisible(True)
            self.setSliceBounds()
        else:  # pass
            self.sl.set_allvisible(False)
            self.setPassBounds()


class ExternalNode(gpi.NodeAPI):
    """A module for slicing, cropping and masking n-D numpy arrays.

    INPUT - input array

    OUTPUTS: note the "out" port is the data you typically want, while the "mask" port shows where that data came from
    out - data after cropping or slicing - size may be different than input array
    mask - copy of input array (same size), but data replaced with zeros wherever data were cropped/sliced

    WIDGETS:
    I/O info: - shows size of input, output arrays
    Dimension[i]
      C/W - sliders select the center and width of cropping range along the ith dimension
      B/E - sliders select the beginning and end of cropping range along the ith dimension
      Slice - slider selects the index to slice along the ith dimension
      Pass - ith dimension is passed (not affected)
    Mask - generate data for "mask" output - good to leave off for large data sets if not needed
    Compute - generate sliced/cropped data

    The Reduce Widget takes a dict with the following keys:
        d = {}
        d['selection'] # integer 0-3 for 'C/W', 'B/E', 'Slice' and 'Pass'

        d['center']    # integer 1-N only for 'C/W'
        d['width']     # integer 1-N only for 'C/W'

        d['floor']     # integer 1-N only for 'B/E'
        d['ceiling']   # integer 1-N only for 'B/E'
    Not all keys have to be present.
    """
    def execType(self):
        '''Could be GPI_THREAD, GPI_PROCESS, GPI_APPLOOP'''
        return gpi.GPI_PROCESS

    def initUI(self):

        # Widgets
        self.addWidget('TextBox', 'I/O Info:')

        self.dim_base_name = 'Dimension['
        self.ndim = 10
        for i in range(self.ndim):
            self.addWidget('ReduceSliders', self.dim_base_name+str(-i-1)+']')
        self.addWidget('PushButton', 'Mask', toggle=True)
        self.addWidget('PushButton', 'Compute', toggle=True, val=True)

        # IO Ports
        self.addInPort('in', 'NPYarray', obligation=gpi.REQUIRED)
        self.addOutPort('out', 'NPYarray')
        self.addOutPort('mask', 'NPYarray')

    def validate(self):
        '''update the widget bounds based on the input data
        '''

        # only update bounds if the 'in' port changed.
        if 'in' in self.portEvents():

            data = self.getData('in')
            dilen = len(data.shape)

            # visibility and bounds
            for i in range(self.ndim):
                if i < dilen:
                    self.setAttr(self.dim_base_name+str(-i-1)+']', visible=True)
                    self.setAttr(self.dim_base_name+str(-i-1)+']', quietmax=data.shape[-i-1])

                    # JGP for Pass, always max out floor and ceiling always
                    w = self.getVal(self.dim_base_name+str(-i-1)+']')
                    if w['selection'] == 3:
                      wmax = data.shape[i]
                      w['center'] = (wmax+1)//2
                      w['width'] = wmax
                      w['floor'] = 1
                      w['ceiling'] = wmax
                      self.setAttr(self.dim_base_name+str(-i-1)+']', quietval=w)
                else:
                    self.setAttr(self.dim_base_name+str(-i-1)+']',
                            visible=False)

        return(0)

    def compute(self):

        if self.getVal('Compute'):

            data = self.getData('in')
            dilen = len(data.shape)

            # setup slicer
            xi = []
            for i in range(dilen-1, -1, -1):
                w = self.getVal(self.dim_base_name+str(-i-1)+']')
                if w['selection'] == 3:  # pass
                    xi.append(slice(None))
                elif w['selection'] == 2:  # slice
                    xi.append(w['center']-1)
                else:  # C/W & B/E
                    xi.append(slice(w['floor']-1, w['ceiling']))

            # apply indices to the data
            out = data[tuple(xi)]

            # update UI info
            self.setAttr('I/O Info:', val="input: "+str(data.shape)
                    +"\noutput: "+str(out.shape))

            self.setData('out', out)

            # do mask operations
            if self.getVal('Mask'):
                mask = data.copy()
                mask[xi] = 0
                self.setData('mask', mask)

        return(0)
