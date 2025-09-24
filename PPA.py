# -*- coding: utf-8 -*-
"""
Created on Sun Oct 12 22:40:05 2014

@author: Themos Tsikas, Jack Richmond
"""

from __future__ import print_function
import os
import sys
import platformdirs
import PPA_lib
from tkinter import Frame, Tk, Menu, Label, Entry, PhotoImage
from tkinter import Scrollbar, Toplevel, Canvas, Radiobutton
from tkinter import Button, LabelFrame, Checkbutton, Scale
from tkinter import HORIZONTAL


def resource_path(relative_path):
    """ Get absolute path to bundled resources """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    # Return unbundled path in dev
    return os.path.join(os.path.abspath("."), relative_path)


def get_cache_file_path(cache_file_name: str = "") -> str:
    """ Gets the best cache file path for system. """
    dir = platformdirs.user_cache_dir("PPA", appauthor=False, ensure_exists=True)
    if cache_file_name == "":
        return dir
    return os.path.join(dir, cache_file_name)


def help_f():
    '''
    Our help window
    '''
    import tkinter.messagebox
    tkinter.messagebox.showinfo("Help", "Visit https://github.com/SudoWatson/PhotoPolarAlign for help.")


def about_f():
    '''
    Our about window
    '''
    import tkinter.messagebox
    tkinter.messagebox.showinfo('About',
                                'PhotoPolarAlign v1.1.0 \n' +
                                'Visit https://github.com/SudoWatson/PhotoPolarAlign for more information')


def clear_cache_f():
    '''
    Confirmation window for clearing cache
    '''
    import tkinter.messagebox
    if tkinter.messagebox.askyesno('Clear Cache?',
                                   "This will permanently delete all files in '" + get_cache_file_path() + "'. Are you sure you wish to continue?"):
        import shutil
        shutil.rmtree(get_cache_file_path())


def wid_hei_frm_header(head):
    '''
    look in header for width and height of image
   '''
    try:
        # nova's wcs files have IMAGEW / IMAGEH
        width = head['IMAGEW']
        height = head['IMAGEH']
        return width, height
    except KeyError:
        try:
            # AstroArt's fits files have NAXIS1 / NAXIS2
            width = head['NAXIS1']
            height = head['NAXIS2']
            return width, height
        except KeyError:
            return 0, 0


def decdeg2dms(dd):
    mnt, sec = divmod(dd * 3600, 60)
    deg, mnt = divmod(mnt, 60)
    return deg, mnt, sec


def cross(crd, img, colour):
    '''
    Annotate with a cross for the RA axis
    '''
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    coords = crd[0]
    ax1 = coords[0]
    ay1 = coords[1]
    draw.line((ax1 - 30, ay1 - 30) + (ax1 + 30, ay1 + 30),
              fill=colour, width=3)
    draw.line((ax1 + 30, ay1 - 30) + (ax1 - 30, ay1 + 30),
              fill=colour, width=3)


def circle(centre, img, colour, name):
    '''
    Annotate with a circle
    '''
    from PIL import ImageFont, ImageDraw
    font = ImageFont.load(resource_path('assets/fonts/symb24.pil'))
    draw = ImageDraw.Draw(img)
    cen = centre[0]
    ax1 = cen[0]
    ay1 = cen[1]
    draw.ellipse((ax1 - 20, ay1 - 20, ax1 + 20, ay1 + 20),
                 fill=None, outline=colour)
    draw.text((ax1 + 30, ay1), name, fill=colour, font=font)


def cpcircle(centre, img, scl):
    '''
    Annotate with target circles
    '''
    from PIL import ImageFont, ImageDraw
    font = ImageFont.load(resource_path('assets/fonts/helvR24.pil'))
    draw = ImageDraw.Draw(img)
    cen = centre[0]
    ax1 = cen[0]
    ay1 = cen[1]
    number = [5, 10, 20, 40]
    for i in number:
        rad = (i * 60) / scl
        draw.ellipse((ax1 - rad, ay1 - rad, ax1 + rad, ay1 + rad),
                     fill=None, outline='Green')
        draw.text((ax1 + (rad * 26) / 36, ay1 + (rad * 26 / 36)), str(i) + "'", formatfont=font)
    draw.line((ax1 - 30, ay1) + (ax1 - 4, ay1), fill='Green', width=2)
    draw.line((ax1 + 4, ay1) + (ax1 + 30, ay1), fill='Green', width=2)
    draw.line((ax1, ay1 - 30) + (ax1, ay1 - 4), fill='Green', width=2)
    draw.line((ax1, ay1 + 4) + (ax1, ay1 + 30), fill='Green', width=2)


class PhotoPolarAlign(Frame):
    '''
    Our application as a class
    '''

    def stat_bar(self, txt):
        '''
        Update the Status bar
        '''
        self.stat_msg = txt
        self.wstat.config(text=self.stat_msg)
        self.wstat.update()

    def settings_destroy(self):
        '''
        User asked to close the Settings
        '''
        PPA_lib.write_config_file(self)
        self.wvar4.configure(text=('%.3s...........' % self.apikey.get()))
        self.settings_win.destroy()

    def settings_open(self):
        '''
        Our Settings window
        '''
        # create child window
        win = Toplevel()
        self.settings_win = win
        win.geometry('480x600')
        win.title('Settings')
        # get the API key information
        frm = LabelFrame(win, borderwidth=2, relief='ridge', text='nova.astrometry.net')
        frm.pack(side='top', ipadx=20, padx=20, fill='x')
        nxt = Label(frm, text='API Key')
        nxt.grid(row=0, column=0, pady=4, sticky='w')
        nxt = Entry(frm, textvariable=self.apikey)
        nxt.grid(row=0, column=1, pady=4)
        nxt = Label(frm, text='Restrict scale')
        nxt.grid(row=1, column=0, pady=4, sticky='w')
        nxt = Checkbutton(frm, var=self.restrict_scale)
        nxt.grid(row=1, column=1, pady=4)

        frm = LabelFrame(win, borderwidth=2, relief='ridge', text='Local solver Configuration')
        frm.pack(side='top', ipadx=20, padx=20, fill='x')

        nxt = Label(frm, text='shell')
        nxt.grid(row=0, column=0, pady=4, sticky='w')
        nxt = Entry(frm, textvariable=self.local_shell, width=0)
        nxt.grid(row=0, column=1, pady=4, sticky='we', columnspan=2)

        ifrm = Frame(frm, bd=0)
        ifrm.grid(row=1, column=0, pady=4, sticky='w', columnspan=3)
        nxt = Label(ifrm, text='downscale')
        nxt.pack(side='left')
        nxt = Radiobutton(ifrm, variable=self.local_downscale, value='1', text='1')
        nxt.pack(side='left')
        nxt = Radiobutton(ifrm, variable=self.local_downscale, value='2', text='2')
        nxt.pack(side='left')
        nxt = Radiobutton(ifrm, variable=self.local_downscale, value='4', text='4')
        nxt.pack(side='left')

        nxt = Label(frm, text='configfile')
        nxt.grid(row=2, column=0, pady=4, sticky='w')
        nxt = Entry(frm, textvariable=self.local_configfile, width=0)
        nxt.grid(row=2, column=1, pady=4, sticky='we', columnspan=2)

        ifrm = Frame(frm, bd=0)
        ifrm.grid(row=3, column=0, pady=4, sticky='w', columnspan=3)
        nxt = Label(ifrm, text='scale_units')
        nxt.pack(side='left')
        nxt = Radiobutton(ifrm, variable=self.local_scale_units, value='arcsecperpix', text='arcsec/pix')
        nxt.pack(side='left')
        nxt = Radiobutton(ifrm, variable=self.local_scale_units, value='degwidth', text='degrees width')
        nxt.pack(side='left')
        nxt = Radiobutton(ifrm, variable=self.local_scale_units, value='arcminwidth', text='arcminutes width')
        nxt.pack(side='left')

        nxt = Label(frm, text='scale_low')
        nxt.grid(row=4, column=0, pady=4, sticky='w')
        nxt = Scale(frm, from_=0, to_=40, orient=HORIZONTAL,
                    variable=self.local_scale_low, showvalue=0, digits=4,
                    sliderlength=10, length=300, resolution=0.1)
        nxt.grid(row=4, column=1, pady=4)
        nxt = Entry(frm, textvariable=self.local_scale_low, width=8)
        nxt.grid(row=4, column=2, pady=4)
        nxt = Label(frm, text='scale_hi')
        nxt.grid(row=5, column=0, pady=4, sticky='w')
        nxt = Scale(frm, from_=0, to_=120, orient=HORIZONTAL,
                    variable=self.local_scale_hi, showvalue=0, digits=4,
                    sliderlength=10, length=300, resolution=0.1)
        nxt.grid(row=5, column=1, pady=4)
        nxt = Entry(frm, textvariable=self.local_scale_hi, width=8)
        nxt.grid(row=5, column=2, pady=4)

        nxt = Label(frm, text='extra')
        nxt.grid(row=6, column=0, pady=4, sticky='w')
        nxt = Entry(frm, textvariable=self.local_xtra, width=40)
        nxt.grid(row=6, column=1, pady=4, sticky='we', columnspan=2)

        nxt = Button(frm, text='Read from AstroTortilla configuration',
                     command=self.slurpAT)
        nxt.grid(row=7, column=0, pady=4, sticky='we', columnspan=3)

        Button(win, text='OK', command=self.settings_destroy).pack(pady=4)

    def quit_method(self):
        '''
        User wants to quit
        '''
        PPA_lib.write_config_file(self)
        self.myparent.destroy()

    def get_file(self, hint):
        '''
        User wants to select an image file
        '''
        import tkinter.filedialog
        from os.path import splitext, dirname, basename
        options = {}
        options['filetypes'] = [('JPEG files', '.jpg .jpeg .JPG .JPEG'),
                                ('all files', '.*')]
        options['initialdir'] = self.imgdir
        titles = {}
        titles['v'] = 'The vertical image of the Celestial Pole region'
        titles['h'] = 'The horizontal image of the Celestial Pole region'
        titles['i'] = 'The horizontal image after Alt/Az adjustment'
        options['title'] = titles[hint]
        img = tkinter.filedialog.askopenfilename(**options)
        if img:
            wcs = get_cache_file_path(os.path.basename(splitext(img)[0] + '.wcs'))
            if PPA_lib.happy_with(wcs, img):
                self.update_solved_labels(hint, 'active')
            else:
                self.update_solved_labels(hint, 'disabled')
            self.imgdir = dirname(img)
            if hint == 'v':
                self.vimg_fn = img
                self.vwcs_fn = wcs
                self.havev = True
                self.wvar1.configure(text=basename(img))
                self.wvfn.configure(bg='green', activebackground='green')
            elif hint == 'h':
                self.himg_fn = img
                self.hwcs_fn = wcs
                self.haveh = True
                self.wvar2.configure(text=basename(img))
                self.whfn.configure(bg='green', activebackground='green')
            elif hint == 'i':
                self.iimg_fn = img
                self.iwcs_fn = wcs
                self.havei = True
                self.wvar3.configure(text=basename(img))
                self.wifn.configure(bg='green', activebackground='green')

    def update_scale(self, hint):
        PPA_lib.update_scale(self, hint)

        if self.havescale:
            self.wvar5.configure(text=('%.2f' % self.scale))
        else:
            self.wvar5.configure(text='--.--')

    def solve(self, hint, solver):
        '''
        Solve an image
        '''
        self.stat_bar('Solving image...')
        if hint != 'i' and self.vimg_fn == self.himg_fn:
            self.stat_bar(('Image filenames coincide - Check the Image filenames'))
            return
        try:
            PPA_lib.solve(self, hint, solver)
        except IOError:
            self.stat_bar(("couldn't open the image - Check the Image filename"))

    def update_display(self, cpcrd, the_scale):
        '''
        update Computed displayed quantities
        '''
        import numpy
        axis = self.axis
        x1a = axis[0]
        y1a = axis[1]
        x2a = cpcrd[0][0]
        y2a = cpcrd[0][1]
        self.scale = the_scale
        self.havescale = True
        self.wvar5.configure(text=('%.2f' % the_scale))
        self.wvar6.configure(text=str(int(x1a))+','+str(int(y1a)))
        self.wvar7.configure(text=(str(int(x2a)) +',' + str(int(y2a))))
        err = the_scale * numpy.sqrt((x1a - x2a)**2 + (y1a - y2a)**2) / 60.0
        self.wvar8.configure(text=('%.2f' % err))
        if x2a > x1a:
            inst = 'Right '
        else:
            inst = 'Left '
        ddeg = abs(x2a - x1a) * the_scale / 3600.0
        inst = inst + ('%02d:%02d:%02d' % decdeg2dms(ddeg))
        self.wvar9.configure(text=inst)
        if y2a > y1a:
            inst = inst + ' Down '
        else:
            inst = inst + ' Up '
        ddeg = abs(y2a - y1a) * the_scale / 3600.0
        inst = inst + ('%02d:%02d:%02d' % decdeg2dms(ddeg))
        self.wvar9.configure(text=inst)

    def annotate_imp(self):
        '''
        Annotate the improvement image
        '''
        from PIL import Image
        from astropy.time import Time
        from astropy.coordinates import SkyCoord
        from astropy.coordinates import FK5
        from astropy.io import fits
        from astropy import wcs
        import numpy
        from os.path import splitext
        if self.iimg_fn == self.himg_fn:
            self.stat_bar(('Image filenames coincide - Check the Image ' +
                           'filenames'))
            return
        try:
            imi = Image.open(self.iimg_fn)
            # Load the FITS hdulist using astropy.io.fits
            hdulisti = fits.open(self.iwcs_fn)
            hdulisth = fits.open(self.hwcs_fn)
        except IOError:
            return
        axis = self.axis
        try:
            axis[0]
        except:
            self.stat_bar("don't know where Polar Axis is - Find Polar Axis")
            return
        self.stat_bar('Annotating...')
        headi = hdulisti[0].header
        headh = hdulisth[0].header
        wcsi = wcs.WCS(headi)
        now = Time.now()
        if self.hemi == 'N':
            cp = SkyCoord(ra=0, dec=90, frame='fk5', unit='deg', equinox=now)
        else:
            cp = SkyCoord(ra=0, dec=-90, frame='fk5', unit='deg', equinox=now)
        cpj2000 = cp.transform_to(FK5(equinox='J2000'))
        cpskycrd = numpy.array([[cpj2000.ra.deg, cpj2000.dec.deg]],
                               numpy.float64)
        cpcrdi = wcsi.wcs_world2pix(cpskycrd, 1)
        scalei = PPA_lib.scale_frm_header(headi)
        widthi, heighti = wid_hei_frm_header(headi)
        if wid_hei_frm_header(headi) != wid_hei_frm_header(headh) :
            self.stat_bar('Incompatible image dimensions...')
            return
        if PPA_lib.parity_frm_header(headi) == 0 :
            self.stat_bar('Wrong parity...')
            return
        self.update_display(cpcrdi, scalei)
        cpcircle(cpcrdi, imi, scalei)
        cross([axis], imi, 'Red')
        if self.hemi == 'N':
            poli = wcsi.wcs_world2pix(self.polaris, 1)
            lami = wcsi.wcs_world2pix(self.lam, 1)
            circle(poli, imi, 'White', 'a')
            circle(lami, imi, 'Orange', 'l')
            left = int(min(cpcrdi[0][0], poli[0][0], lami[0][0], axis[0]))
            right = int(max(cpcrdi[0][0], poli[0][0], lami[0][0], axis[0]))
            bottom = int(min(cpcrdi[0][1], poli[0][1], lami[0][1], axis[1]))
            top = int(max(cpcrdi[0][1], poli[0][1], lami[0][1], axis[1]))
        else:
            ori = wcsi.wcs_world2pix(self.chi, 1)
            whi = wcsi.wcs_world2pix(self.sigma, 1)
            rei = wcsi.wcs_world2pix(self.red, 1)
            circle(whi, imi, 'White', 's')
            circle(ori, imi, 'Orange', 'c')
            circle(rei, imi, 'Red', '!')
            left = int(min(cpcrdi[0][0], ori[0][0], whi[0][0], axis[0]))
            right = int(max(cpcrdi[0][0], ori[0][0], whi[0][0], axis[0]))
            bottom = int(min(cpcrdi[0][1], ori[0][1], whi[0][1], axis[1]))
            top = int(max(cpcrdi[0][1], ori[0][1], whi[0][1], axis[1]))
        margin = int(2500 / scalei)
        xl = max(1, left - margin)
        xr = min(widthi, right + margin)
        yt = min(heighti, top + margin)
        yb = max(1, bottom - margin)
        croppedi = imi.crop((xl, yb, xr, yt))
        croppedi.load()
        crop_fn = get_cache_file_path(os.path.basename(os.path.splitext(self.himg_fn)[0] + '_cropi.ppm'))
        croppedi.save(crop_fn, 'PPM')
        self.create_imgwin(crop_fn, self.iimg_fn)
        self.stat_bar('Idle')

    def annotate(self):
        '''
        Find RA axis and Annotate the pair of horiz/vertical images
        '''
        from PIL import Image
        from astropy.time import Time
        import scipy.optimize
        from astropy.coordinates import SkyCoord
        from astropy.coordinates import FK5
        from astropy.io import fits
        from astropy import wcs
        import numpy

        if self.vimg_fn == self.himg_fn:
            self.stat_bar(('Image filenames coincide - Check the Image ' +
                           'filenames'))
            return
        try:
            imh = Image.open(self.himg_fn)
            # Load the FITS hdulist using astropy.io.fits
            hdulistv = fits.open(self.vwcs_fn)
            hdulisth = fits.open(self.hwcs_fn)
        except IOError:
            return
        self.stat_bar('Finding RA axis...')
        # Parse the WCS keywords in the primary HDU
        headv = hdulistv[0].header
        headh = hdulisth[0].header
        wcsv = wcs.WCS(headv)
        wcsh = wcs.WCS(headh)
        decv = PPA_lib.dec_frm_header(headv)
        dech = PPA_lib.dec_frm_header(headh)
        if decv > 65 and dech > 65:
            self.hemi = 'N'
        elif decv < -65 and dech < -65:
            self.hemi = 'S'
        else:
            self.stat_bar('Nowhere near (>25 deg) the Poles!')
            return
        now = Time.now()
        if self.hemi == 'N':
            cp = SkyCoord(ra=0, dec=90, frame='fk5', unit='deg', equinox=now)
        else:
            cp = SkyCoord(ra=0, dec=-90, frame='fk5', unit='deg', equinox=now)

        # CP now, in J2000 coordinates, precess
        cpj2000 = cp.transform_to(FK5(equinox='J2000'))
        # sky coordinates
        cpskycrd = numpy.array([[cpj2000.ra.deg, cpj2000.dec.deg]],
                               numpy.float64)
        # pixel coordinates
        cpcrdh = wcsh.wcs_world2pix(cpskycrd, 1)
        if self.hemi == 'N':
            print('Northern Celestial Pole', dech)
        else:
            print('Southern Celestial Pole', dech)
        scaleh = PPA_lib.scale_frm_header(headh)
        widthh, heighth = wid_hei_frm_header(headh)
        if wid_hei_frm_header(headh) != wid_hei_frm_header(headv):
            self.stat_bar('Incompatible image dimensions...')
            return
        if PPA_lib.parity_frm_header(headh) == 0 or PPA_lib.parity_frm_header(headv) == 0:
            self.stat_bar('Wrong parity...')
            return

        def displacement(coords):
            '''
            the movement of a sky object in the two images
            '''
            pixcrd1 = numpy.array([coords], numpy.float64)
            skycrd = wcsv.wcs_pix2world(pixcrd1, 1)
            pixcrd2 = wcsh.wcs_world2pix(skycrd, 1)
            return pixcrd2 - pixcrd1
        axis = scipy.optimize.broyden1(displacement, [widthh/2, heighth/2])
        self.axis = axis
        self.update_display(cpcrdh, scaleh)
        #
        self.stat_bar('Annotating...')
        cpcircle(cpcrdh, imh, scaleh)
        cross([axis], imh, 'Red')
        # add reference stars
        if self.hemi == 'N':
            polh = wcsh.wcs_world2pix(self.polaris, 1)
            lamh = wcsh.wcs_world2pix(self.lam, 1)
            circle(polh, imh, 'White', 'a')
            circle(lamh, imh, 'Orange', 'l')
            left = int(min(cpcrdh[0][0], polh[0][0], lamh[0][0], axis[0]))
            right = int(max(cpcrdh[0][0], polh[0][0], lamh[0][0], axis[0]))
            bottom = int(min(cpcrdh[0][1], polh[0][1], lamh[0][1], axis[1]))
            top = int(max(cpcrdh[0][1], polh[0][1], lamh[0][1], axis[1]))
        else:
            orh = wcsh.wcs_world2pix(self.chi, 1)
            whh = wcsh.wcs_world2pix(self.sigma, 1)
            reh = wcsh.wcs_world2pix(self.red, 1)
            circle(whh, imh, 'White', 's')
            circle(orh, imh, 'Orange', 'c')
            circle(reh, imh, 'Red', '!')
            left = int(min(cpcrdh[0][0], orh[0][0], whh[0][0], axis[0]))
            right = int(max(cpcrdh[0][0], orh[0][0], whh[0][0], axis[0]))
            bottom = int(min(cpcrdh[0][1], orh[0][1], whh[0][1], axis[1]))
            top = int(max(cpcrdh[0][1], orh[0][1], whh[0][1], axis[1]))
        margin = int(2500 / scaleh)
        xl = max(1, left - margin)
        xr = min(widthh, right + margin)
        yt = min(heighth, top + margin)
        yb = max(1, bottom - margin)
        croppedh = imh.crop((xl, yb, xr, yt))
        croppedh.load()
        crop_fn = get_cache_file_path(os.path.basename(os.path.splitext(self.himg_fn)[0] + '_croph.ppm'))
        croppedh.save(crop_fn, 'PPM')
        self.create_imgwin(crop_fn, self.himg_fn)
        self.stat_bar('Idle')

    def create_imgwin(self, img_fn, title):
        '''
        creates a window to display an image
        '''
        from os.path import basename
        # create child window
        img = PhotoImage(file=img_fn)
        win = Toplevel()
        wwid = min(800, img.width())
        whei = min(800, img.height())
        win.geometry(('%dx%d' % (wwid + 28, whei + 28)))
        win.title(basename(title))
        frame = Frame(win, bd=0)
        frame.pack()
        xscrollbar = Scrollbar(frame, orient='horizontal')
        xscrollbar.pack(side='bottom', fill='x')
        yscrollbar = Scrollbar(frame, orient='vertical')
        yscrollbar.pack(side='right', fill='y')
        canvas = Canvas(frame, bd=0, width=wwid, height=whei,
                        scrollregion=(0, 0, img.width(), img.height()),
                        xscrollcommand=xscrollbar.set,
                        yscrollcommand=yscrollbar.set)
        canvas.pack(side='top', fill='both', expand=1)
        canvas.create_image(0, 0, image=img, anchor='nw')
        xscrollbar.config(command=canvas.xview)
        yscrollbar.config(command=canvas.yview)
        frame.pack()
        # next statement is important! creates reference to img
        canvas.img = img

    def update_solved_labels(self, hint, sta):
        '''
        updates displayed Solved labels
        '''
        if hint == 'v':
            widget = self.wvok
        elif hint == 'h':
            widget = self.whok
        elif hint == 'i':
            widget = self.wiok
        # oldstate = widget.config()['state'][4]
        if (sta == 'active'):
            widget.configure(state='active', bg='green',
                             activebackground='green',
                             highlightbackground='green')
        elif (sta == 'disabled'):
            widget.configure(state='disabled', bg='red',
                             activebackground='red',
                             highlightbackground='red')
        widget.update()

    def slurpAT(self):
        import tkinter.filedialog
        import configparser
        self.stat_bar('Reading...')
        options = {}
        options['filetypes'] = [('Config files', '.cfg'),
                                ('all files', '.*')]
        options['initialdir'] = self.imgdir
        options['title'] = 'The AstroTortilla configuration file'
        cfg_fn = tkinter.filedialog.askopenfilename(**options)
        config = configparser.ConfigParser()
        config.read(cfg_fn)
        for s in config.sections():
            if s == 'Solver-AstrometryNetSolver':
                for o in config.options(s):
                    if o == 'configfile':
                        self.local_configfile.set(config.get(s, o))
                    elif o == 'shell':
                        self.local_shell.set(config.get(s, o))
                    elif o == 'downscale':
                        self.local_downscale.set(config.getint(s, o))
                    elif o == 'scale_units':
                        self.local_scale_units.set(config.get(s, o))
                    elif o == 'scale_low':
                        self.local_scale_low.set(config.getfloat(s, o,))
                    elif o == 'scale_max':
                        self.local_scale_hi.set(config.getfloat(s, o))
                    elif o == 'xtra':
                        self.local_xtra.set(config.get(s, o,))

        self.stat_bar('Idle')
        return

    def create_widgets(self, master):
        '''
        creates the main window components
        '''
        self.myparent = master
        self.myparent.title('Photo Polar Alignment')
        #
        self.menubar = Menu(master)
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.helpmenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='File', menu=self.filemenu)
        self.menubar.add_cascade(label='Help', menu=self.helpmenu)
        self.filemenu.add_command(label='Settings...',
                                  command=self.settings_open)
        self.filemenu.add_command(label='Clear cache',
                                  command=clear_cache_f)
        self.filemenu.add_command(label='Exit', command=self.quit_method)
        self.helpmenu.add_command(label='Help', command=help_f)
        self.helpmenu.add_command(label='About...', command=about_f)
        self.myparent.config(menu=self.menubar)
        # #################################################################
        self.wfrop = LabelFrame(master, text='Operations')
        self.wfrop.pack(side='top', fill='x')
        #
        nxt = Button(self.wfrop, image=self.vicon, command=lambda: self.get_file('v'))
        nxt.grid(row=0, column=0, sticky='ew', padx=10, pady=4, rowspan=3)
        self.wvfn = nxt
        nxt = Button(self.wfrop, text='Nova', command=lambda: self.solve('v', 'nova'))
        nxt.grid(row=0, column=1, sticky='ew', padx=10, pady=4)
        self.wvsol = nxt
        nxt = Button(self.wfrop, text='Local', command=lambda: self.solve('v', 'local'))
        nxt.grid(row=1, column=1, sticky='ew', padx=10, pady=4)
        self.wlvsol = nxt
        nxt = Label(self.wfrop, text='Solved', state='disabled')
        nxt.grid(row=2, column=1, sticky='ew', padx=10, pady=4)
        self.wvok = nxt
        #
        nxt = Button(self.wfrop, image=self.hicon, command=lambda: self.get_file('h'))
        nxt.grid(row=3, column=0, sticky='ew', padx=10, pady=4, rowspan=3)
        self.whfn = nxt
        nxt = Button(self.wfrop, text='Nova', command=lambda: self.solve('h', 'nova'))
        nxt.grid(row=3, column=1, sticky='ew', padx=10, pady=4)
        self.whsol = nxt
        nxt = Button(self.wfrop, text='Local', command=lambda: self.solve('h', 'local'))
        nxt.grid(row=4, column=1, sticky='ew', padx=10, pady=4)
        self.wlhsol = nxt
        nxt = Label(self.wfrop, text='Solved', state='disabled')
        nxt.grid(row=5, column=1, sticky='ew', padx=10, pady=4)
        self.whok = nxt
        #
        nxt = Button(self.wfrop, text='Find Polar Axis',
                     command=self.annotate)
        nxt.grid(row=6, column=0, sticky='ew', padx=10, pady=4, columnspan=2)
        self.wann = nxt
        #
        nxt = Button(self.wfrop, image=self.iicon, command=lambda: self.get_file('i'))
        nxt.grid(row=3, column=3, sticky='ew', padx=10, pady=4, rowspan=3)
        self.wifn = nxt
        nxt = Button(self.wfrop, text='Nova', command=lambda: self.solve('i', 'nova'))
        nxt.grid(row=3, column=4, sticky='ew', padx=10, pady=4)
        self.wisol = nxt
        nxt = Button(self.wfrop, text='Local', command=lambda: self.solve('i', 'local'))
        nxt.grid(row=4, column=4, sticky='ew', padx=10, pady=4)
        self.wlisol = nxt
        nxt = Label(self.wfrop, text='Solved', state='disabled')
        nxt.grid(row=5, column=4, sticky='ew', padx=10, pady=4)
        self.wiok = nxt
        #
        nxt = Button(self.wfrop, text='Show Improvement',
                     command=self.annotate_imp)
        nxt.grid(row=6, column=3, sticky='ew', padx=10, pady=4, columnspan=2)
        self.wanni = nxt
        # #################################################################

        nxt = LabelFrame(master, borderwidth=2, relief='ridge',
                         text='Info')
        nxt.pack(side='top', fill='x')
        self.wfrvar = nxt
        nxt = Label(self.wfrvar, text='Given')
        nxt.grid(row=0, column=1, columnspan=2, sticky='w')
        nxt = Label(self.wfrvar, anchor='w', text='Vertical:')
        nxt.grid(row=1, column=0, sticky='w')
        nxt = Label(self.wfrvar, text='---------')
        nxt.grid(row=1, column=1, sticky='e')
        self.wvar1 = nxt
        nxt = Label(self.wfrvar, text='Horizontal:')
        nxt.grid(row=2, column=0, sticky='w')
        nxt = Label(self.wfrvar, text='---------')
        nxt.grid(row=2, column=1, sticky='e')
        self.wvar2 = nxt
        nxt = Label(self.wfrvar, text='Improved:')
        nxt.grid(row=3, column=0, sticky='w')
        nxt = Label(self.wfrvar, text='---------')
        nxt.grid(row=3, column=1, sticky='e')
        self.wvar3 = nxt
        nxt = Label(self.wfrvar, text='API key:')
        nxt.grid(row=4, column=0, sticky='w')
        nxt = Label(self.wfrvar, text=('%.3s...........' % self.apikey.get()))
        nxt.grid(row=4, column=1, sticky='e')
        self.wvar4 = nxt

        nxt = Label(self.wfrvar, text='                ')  # Spacing between columns
        nxt.grid(row=0, column=2, columnspan=1, sticky='w')

        nxt = Label(self.wfrvar, text='Computed')
        nxt.grid(row=0, column=4, columnspan=2, sticky='w')
        nxt = Label(self.wfrvar, text='Scale (arcsec/pixel):')
        nxt.grid(row=1, column=3, sticky='w')
        if self.havescale:
            nxt = Label(self.wfrvar, text=self.scale)
        else:
            nxt = Label(self.wfrvar, text='--.--')
        nxt.grid(row=1, column=4, sticky='e')
        self.wvar5 = nxt
        nxt = Label(self.wfrvar, text='RA axis position:')
        nxt.grid(row=2, column=3, sticky='w')
        nxt = Label(self.wfrvar, text='---,---')
        nxt.grid(row=2, column=4, sticky='e')
        self.wvar6 = nxt
        nxt = Label(self.wfrvar, text='CP position:')
        nxt.grid(row=3, column=3, sticky='w')
        nxt = Label(self.wfrvar, text='---,---')
        nxt.grid(row=3, column=4, sticky='e')
        self.wvar7 = nxt
        nxt = Label(self.wfrvar, text='Error (arcmin):')
        nxt.grid(row=4, column=3, sticky='w')
        nxt = Label(self.wfrvar, text='--.--')
        nxt.grid(row=4, column=4, sticky='e')
        self.wvar8 = nxt
        # #################################################################
        nxt = LabelFrame(master, borderwidth=2, relief='ridge',
                         text='Move (dd:mm:ss)')
        nxt.pack(side='top', fill='x')
        self.wfrmo = nxt
        nxt = Label(self.wfrmo, anchor='center', font='-weight bold -size 14')
        nxt.pack(anchor='center')
        self.wvar9 = nxt
        # #################################################################
        nxt = LabelFrame(master, borderwidth=2, relief='ridge', text='Status')
        nxt.pack(side='bottom', fill='x')
        self.wfrst = nxt
        nxt = Label(self.wfrst, anchor='w', text=self.stat_msg)
        nxt.pack(anchor='w')
        self.wstat = nxt

    # Some CLI
    def __init__(self, master=None):
        PPA_lib.init_ppa(self)
        master.geometry(self.usergeo)

        # the filenames of images
        self.vimg_fn = ''
        self.havev = False
        self.himg_fn = ''
        self.haveh = False
        self.iimg_fn = ''
        self.havei = False
        # the filenames of the .wcs solutions
        self.vwcs_fn = ''
        self.hwcs_fn = ''
        self.iwcs_fn = ''
        # the button icons
        self.vicon = PhotoImage(file=resource_path('assets/v2_2.ppm'))
        self.hicon = PhotoImage(file=resource_path('assets/h2_2.ppm'))
        self.iicon = PhotoImage(file=resource_path('assets/i2_2.ppm'))
        # the solved image scale
        self.havescale = False
        self.scale = None
        # the discovered hemisphere
        self.hemi = None
        # initialise attributes set elsewhere
        self.menubar = None
        self.helpmenu = None
        self.filemenu = None
        self.wfrop = None
        self.wvfn = None
        self.wvsol = None
        self.wlvsol = None
        self.wvok = None

        self.whfn = None
        self.whsol = None
        self.wlhsol = None
        self.whok = None

        self.wifn = None
        self.wisol = None
        self.wlisol = None
        self.wiok = None

        self.wann = None
        self.wanni = None

        self.wfr2 = None
        self.wfrvar = None
        self.wvar1 = None
        self.wvar2 = None
        self.wvar3 = None
        self.wvar4 = None
        self.wfrcomp = None
        self.wvar5 = None
        self.wvar6 = None
        self.wvar7 = None
        self.wvar8 = None

        self.wfrmo = None
        self.wvar9 = None

        self.wfrst = None
        self.wstat = None

        self.myparent = None

        self.stat_msg = 'Idle'
        Frame.__init__(self, master)
        self.create_widgets(master)
        # check local solver
        self.wlvsol.configure(state='disabled')
        self.wlhsol.configure(state='disabled')
        self.wlisol.configure(state='disabled')
        try:
            self.local_shell.set(self.config.get('local', 'shell'))
            self.local_downscale.set(self.config.getint('local', 'downscale'))
            self.local_configfile.set(self.config.get('local', 'configfile'))
            self.local_scale_units.set(self.config.get('local', 'scale_units'))
            self.local_scale_low.set(self.config.getfloat('local', 'scale_low'))
            self.local_scale_hi.set(self.config.getfloat('local', 'scale_hi'))
            self.local_xtra.set(self.config.get('local', 'xtra'))
            # check solve-field cmd
            exit_status = os.system(self.local_shell.get() % 'solve-field > /dev/null')  # TODO: Make this failing not delete all settings
            if exit_status != 0:
                print("Can't use local astrometry.net solver, check PATH")
            else:
                self.wlvsol.configure(state='active')
                self.wlhsol.configure(state='active')
                self.wlisol.configure(state='active')
        except Exception as e:
            print(e)
            self.local_shell.set('')
            self.local_downscale.set(1)
            self.local_configfile.set('')
            self.local_scale_units.set('')
            self.local_scale_low.set(0)
            self.local_scale_hi.set(0)
            self.local_xtra.set('')
        if not self.apikey.get() or self.apikey.get() == '':
            self.settings_open()
        self.pack()


ROOT = Tk()
ROOT.geometry('440x470+300+300')
APP = PhotoPolarAlign(master=ROOT)
ROOT.mainloop()
