import os
import sys
import platformdirs
from urllib.request import urlopen
from tkinter import StringVar, IntVar, DoubleVar  # Replace with non-tkinter types
from NovaClient import NovaClient


class RequestError(Exception):
    '''
    An exception that happens when talking to the plate solver
    '''
    pass


def decdeg2dms(dd):
    mnt, sec = divmod(dd * 3600, 60)
    deg, mnt = divmod(mnt, 60)
    return deg, mnt, sec


def scale_frm_wcs(fn):
    from astropy.io import fits
    hdu = fits.open(fn)
    head = hdu[0].header
    return scale_from_header(head)


def parity_from_header(head):
    '''
    look in the plate-solution header for the parity information
    '''
    try:
        # nova's wcs files have the parity in the comments
        comments = head['COMMENT']
        size = (len(comments))
        for i in range(0, size):
            if comments[i][0:6] == 'parity':
                tkns = comments[i].split(' ')
                return int(tkns[1])
    except KeyError:
        return 1


def scale_from_header(head):
    '''
    look in the plate-solution header for the scale information
    '''
    try:
        # nova's wcs files have the scale in the comments
        comments = head['COMMENT']
        size = (len(comments))
        for i in range(0, size):
            if comments[i][0:5] == 'scale':
                tkns = comments[i].split(' ')
                return float(tkns[1])
    except KeyError:
        try:
            # AstroArt's wcs files have it CDELT1 (deg/pixel)
            cdelt1 = abs(head['CDELT1'])
            return float(cdelt1) * 60.0 * 60.0
        except KeyError:
            return 1.0


def width_height_from_header(head):
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


def dec_frm_header(head):
    '''
    look in header for width and height of image
   '''
    # nova's and AstroArt's wcs files have CRVAL2
    dec = head['CRVAL2']
    return dec


def happy_with(wcs, img):
    '''
    check that .wcs (wcs) is compatible with .jpg (img)
    '''
    if os.path.exists(wcs):
        # DBG print wcs, 'exists'
        # check timestamps
        # DBG print os.stat(wcs).st_atime, os.stat(wcs).st_mtime, os.stat(wcs).st_ctime, 'wcs'
        # DBG print os.stat(img).st_atime, os.stat(img).st_mtime, os.stat(img).st_ctime, 'img'
        if os.stat(wcs).st_mtime > os.stat(img).st_mtime:
            return True
    return False


def get_config_file_path(config_file_name: str = "PPA.ini") -> str:
    """ Gets the best config file path for system. Will prioritize config in working dir over system config dir. """
    path = ""
    for dir in os.curdir, os.path.expanduser("~"), platformdirs.user_config_dir("PPA", appauthor=False, ensure_exists=True):
        if dir is None:
            continue
        path = os.path.join(dir, config_file_name)
        if os.path.exists(path):
            return path
    return path  # Return '~/.config/PPA/ppa.ini' (or whatever system preferred) by default. Will create if doesn't exist


def get_cache_file_path(cache_file_name: str = "") -> str:
    """ Gets the best cache file path for system. """
    dir = platformdirs.user_cache_dir("PPA", appauthor=False, ensure_exists=True)
    if cache_file_name == "":
        return dir
    return os.path.join(dir, cache_file_name)


def get_wcs_file_path(image_file_name: str, cache_dir_override: str = None):
    cache_dir_override = cache_dir_override or get_cache_file_path()
    return os.path.join(cache_dir_override, os.path.basename(os.path.splitext(image_file_name)[0] + '.wcs'))


def write_config_file(ppa):
    '''
    Update the user preferences file
    '''
    # the API key
    if not ppa.config.has_section('nova'):
        ppa.config.add_section('nova')
    ppa.config.set('nova', 'apikey', str(ppa.apikey.get()))
    # the image directory
    if not ppa.config.has_section('file'):
        ppa.config.add_section('file')
    ppa.config.set('file', 'imgdir', str(ppa.imgdir))
    # the geometry
    if not ppa.config.has_section('appearance'):
        ppa.config.add_section('appearance')
    ppa.config.set('appearance', 'geometry',
                   str(ppa.myparent.winfo_geometry()))
    # the operating options
    if not ppa.config.has_section('operations'):
        ppa.config.add_section('operations')
    ppa.config.set('operations', 'restrict scale',
                   str(ppa.restrict_scale.get()))
    # the local solve options
    if not ppa.config.has_section('local'):
        ppa.config.add_section('local')
    ppa.config.set('local', 'shell',
                   str(ppa.local_shell.get()).replace('%', '%%'))  # Need to escape format characters so they get read properly
    ppa.config.set('local', 'downscale',
                   str(ppa.local_downscale.get()))
    ppa.config.set('local', 'configfile',
                   str(ppa.local_configfile.get()))
    ppa.config.set('local', 'scale_units',
                   str(ppa.local_scale_units.get()))
    ppa.config.set('local', 'scale_low',
                   str(ppa.local_scale_low.get()))
    ppa.config.set('local', 'scale_hi',
                   str(ppa.local_scale_hi.get()))
    ppa.config.set('local', 'xtra',
                   str(ppa.local_xtra.get()))

    with open(ppa.cfgfn, 'w') as cfgfile:
        ppa.config.write(cfgfile)
    cfgfile.close()


def update_scale(ppa, hint):
    try:
        if hint == 'v':
            ppa.scale = scale_frm_wcs(ppa.vwcs_fn)
        elif hint == 'h':
            ppa.scale = scale_frm_wcs(ppa.hwcs_fn)
        elif hint == 'i':
            ppa.scale = scale_frm_wcs(ppa.iwcs_fn)
        ppa.havescale = True
    except:
        ppa.havescale = False
        return


def solve(ppa, hint, solver):
    '''
    Solve an image
    '''
    if hint == 'h' or hint == 'v':
        if ppa.vimg_fn == ppa.himg_fn:
            # Throw exception
            return
    if hint == 'h':
        aimg = ppa.himg_fn
        awcs = ppa.hwcs_fn
    elif hint == 'v':
        aimg = ppa.vimg_fn
        awcs = ppa.vwcs_fn
    elif hint == 'i':
        aimg = ppa.iimg_fn
        awcs = ppa.iwcs_fn
    else:
        raise Exception('Invalid hint passed:', hint)

    open(aimg)  # Throw exception IOError if unable to open images

    if solver == 'nova':
        img2wcs(ppa, ppa.apikey.get(), aimg, awcs, hint)
    if solver == 'local':
        local_img2wcs(ppa, aimg, awcs, hint)
    ppa.update_solved_labels(hint, 'active')
    update_scale(ppa, hint)
    ppa.stat_bar('Idle')


def find_ra_axis_pix_coords(v_fits, h_fits):
    '''
    Find RA axis based on 2 images rotated about axis
    '''
    import scipy.optimize
    from astropy import wcs
    import numpy

    # Parse the WCS keywords in the primary HDU
    header_v = v_fits.header
    header_h = h_fits.header
    wcsv = wcs.WCS(header_v)  # TODO: This is the second FITSFixedWarning
    wcsh = wcs.WCS(header_h)

    width_h, height_h = width_height_from_header(header_h)
    if (width_h, height_h) != width_height_from_header(header_v):
        raise Exception("Incompatible image dimensions")
        return
    if parity_from_header(header_h) == 0 or parity_from_header(header_v) == 0:
        print("Parity h: " + str(parity_from_header(header_h)))
        print("Parity v: " + str(parity_from_header(header_v)))
        raise Exception("Wrong parity in images")  # I honestly don't know what this means right now
        return

    def displacement(coords):  # Is the point in the sky at this pixel coordinate in the same pixel coordinate in the other image? Return difference
        '''
        The difference in pixel coordinates from the horiz-vert images
        '''
        pixcrd1 = numpy.array([coords], numpy.float64)
        skycrd = wcsv.wcs_pix2world(pixcrd1, 1)
        pixcrd2 = wcsh.wcs_world2pix(skycrd, 1)
        return pixcrd2 - pixcrd1
    # Finding the point in both images that represent the same point in the sky.
    ra_axis_pix_coords = scipy.optimize.broyden1(displacement, [width_h / 2, height_h / 2])  # Start with initial guess of middle of the image, and keep testing until we get closer and closer to the actual point that is the same in both.
    # ra_axis_sky_coords = wcsv.wcs_pix2world(numpy.array([ra_axis_pix_coords], numpy.float64), 1)

    return ra_axis_pix_coords


def find_error(v_wcs_filename, h_wcs_filename):
    '''
    Find error in RA axis
    '''
    from astropy.time import Time
    from astropy.coordinates import SkyCoord
    from astropy.coordinates import FK5
    from astropy.io import fits
    from astropy import wcs
    import numpy

    # Load the FITS hdulist using astropy.io.fits
    hdulist_v = fits.open(v_wcs_filename)
    hdulist_h = fits.open(h_wcs_filename)

    # Parse the WCS keywords in the primary HDU
    header_v = hdulist_v[0].header
    header_h = hdulist_h[0].header
    decv = dec_frm_header(header_v)
    dech = dec_frm_header(header_h)
    now = Time.now()
    if decv > 65 and dech > 65:
        cp = SkyCoord(ra=0, dec=90, frame='fk5', unit='deg', equinox=now)
    elif decv < -65 and dech < -65:
        cp = SkyCoord(ra=0, dec=-90, frame='fk5', unit='deg', equinox=now)
    else:
        raise Exception("Nowhere near Celestial Pole. Must be <25 degrees")
    # CP now, in J2000 coordinates, precess
    cpj2000 = cp.transform_to(FK5(equinox='J2000'))
    wcsh = wcs.WCS(header_h)  # TODO: Waring about transformation has more axes (2) than image (0)
    cp_sky_coord = numpy.array([[cpj2000.ra.deg, cpj2000.dec.deg]], numpy.float64)
    cp_pixcoord_rel_h = wcsh.wcs_world2pix(cp_sky_coord, 1)  # Pixel coordinates relative to h
    cp_x = cp_pixcoord_rel_h[0][0]
    cp_y = cp_pixcoord_rel_h[0][1]

    axis = find_ra_axis_pix_coords(hdulist_v[0], hdulist_h[0])
    axis_x = axis[0]  # Pixel coords
    axis_y = axis[1]

    # ppa.scale = scaleh
    # ppa.havescale = True
    # error = scaleh * numpy.sqrt((axis_x - cp_x)**2 + (axis_y - cp_y)**2) / 60.0

    scaleh = scale_from_header(header_h)
    error = [abs(cp_x - axis_x) * scaleh / 3600, abs(cp_y - axis_y) * scaleh / 3600]
    return error


def init_ppa(ppa):
    import configparser
    import numpy
    # a F8Ib 2.0 mag star, Alpha Ursa Minoris
    ppa.polaris = numpy.array([[037.954561, 89.264109]], numpy.float64)
    #
    # a M1III 6.4 mag star, Lambda Ursa Minoris
    ppa.lam = numpy.array([[259.235229, 89.037706]], numpy.float64)
    #
    # a F0III 5.4 mag star, Sigma Octans
    ppa.sigma = numpy.array([[317.195164, -88.956499]], numpy.float64)
    #
    # a K3IIICN 5.3 mag star, Chi Octans
    ppa.chi = numpy.array([[283.696388, -87.605843]], numpy.float64)
    #
    # a M1III 7.2 mag star, HD90104
    ppa.red = numpy.array([[130.522862, -89.460536]], numpy.float64)
    #
    # the pixel coords of the RA axis, if solution exists
    ppa.axis = None
    ppa.havea = False
    # the Settings window
    ppa.settings_win = None
    # the User preferences file
    ppa.cfgfn = get_config_file_path()

    ppa.local_shell = StringVar()
    ppa.local_downscale = IntVar()
    ppa.local_configfile = StringVar()
    ppa.local_scale_units = StringVar()
    ppa.local_scale_low = DoubleVar()
    ppa.local_scale_hi = DoubleVar()
    ppa.local_xtra = StringVar()

    # Read the User preferences
    ppa.config = configparser.ConfigParser()
    ppa.config.read(ppa.cfgfn)
    # ...the key
    try:
        k_ini = ppa.config.get('nova', 'apikey')
    except:
        k_ini = None
    ppa.apikey = StringVar(value=k_ini)
    # ...the Image directory
    try:
        ppa.imgdir = ppa.config.get('file', 'imgdir')
    except:
        ppa.imgdir = None
    # ...geometry
    try:
        ppa.usergeo = ppa.config.get('appearance', 'geometry')
    except:
        ppa.usergeo = None
    # do we want to help solves by restricting the scale once we have an estimate
    ppa.restrict_scale = IntVar(value=0)
    try:
        ppa.restrict_scale.set(ppa.config.getint('operations', 'restrict scale'))
    except:
        ppa.restrict_scale.set(0)


def local_img2wcs(ppa, filename, wcsfn, hint):
    import os
    import time
    t_start = time.time()
    # TODO: I seriously don't think this will ever be false unless you're in a really weird situation. Just remove this condition. And the next one.
    if (('OS' in os.environ and os.environ['OS'] == 'Windows_NT') or
        ('OSTYPE' in os.environ and os.environ['OSTYPE'] == 'linux') or
        (os.uname()[0] == 'Linux') or
            ('OSTYPE' in os.environ and os.environ['OSTYPE'] == 'darwin')):
        # Cygwin local or Linux local
        if True:
            # first rough estimate of scale
            print('___________________________________________________________')
            # solve-field provided by Astrometry.net package
            cmd = 'solve-field -b ' + ppa.local_configfile.get()
            if ppa.havescale and ppa.restrict_scale.get() == 1:
                up_lim = ppa.scale * 1.05
                lo_lim = ppa.scale * 0.95
                cmd = cmd + (' -u app -L %.2f -H %.2f ' % (lo_lim, up_lim))
            else:
                cmd = cmd + ' -u ' + ppa.local_scale_units.get()
                cmd = cmd + (' -L %.2f' % ppa.local_scale_low.get())
                cmd = cmd + (' -H %.2f' % ppa.local_scale_hi.get())
            if ppa.local_downscale.get() != 1:
                cmd = cmd + (' -z %d' % ppa.local_downscale.get())
            cmd = cmd + ' ' + ppa.local_xtra.get()
            cmd = cmd + ' -O '
            cmd = cmd + ' -D ' + os.path.dirname(wcsfn)  # Output files to specified cache directory
            cmd = cmd + ' \\"%s\\"'
            template = ((ppa.local_shell.get() % cmd))
            # print template
            cmd = (template % filename)
            print(cmd)
            os.system(cmd)
            print('___________________________________________________________')
    print('local solve time ' + str(time.time() - t_start))
    print('___________________________________________________________')


# Used by GUI. Not much left of use for PPA
def img2wcs(ppa, ankey, filename, wcsfn, hint):
    '''
    Plate solves one image
    '''
    import optparse
    import time
    t_start = time.time()
    parser = optparse.OptionParser()
    parser.add_option('--server', dest='server',
                      default=NovaClient.default_url,
                      help='Set server base URL (eg, %default)')
    parser.add_option('--apikey', '-k', dest='apikey',
                      help='API key for Astrometry.net web service; if not' +
                      'given will check AN_API_KEY environment variable')
    parser.add_option('--upload', '-u', dest='upload', help='Upload a file')
    parser.add_option('--wait', '-w', dest='wait', action='store_true',
                      help='After submitting, monitor job status')
    parser.add_option('--wcs', dest='wcs',
                      help='Download resulting wcs.fits file, saving to ' +
                      'given filename; implies --wait if --urlupload or' +
                      '--upload')
    parser.add_option('--kmz', dest='kmz',
                      help='Download resulting kmz file, saving to given ' +
                      'filename; implies --wait if --urlupload or --upload')
    parser.add_option('--urlupload', '-U', dest='upload_url',
                      help='Upload a file at specified url')
    parser.add_option('--scale-units', dest='scale_units',
                      choices=('arcsecperpix', 'arcminwidth', 'degwidth',
                               'focalmm'),
                      help='Units for scale estimate')
    parser.add_option('--scale-lower', dest='scale_lower', type=float,
                      help='Scale lower-bound')
    parser.add_option('--scale-upper', dest='scale_upper', type=float,
                      help='Scale upper-bound')
    parser.add_option('--scale-est', dest='scale_est', type=float,
                      help='Scale estimate')
    parser.add_option('--scale-err', dest='scale_err', type=float,
                      help='Scale estimate error (in PERCENT), eg "10" if' +
                      'you estimate can be off by 10%')
    parser.add_option('--ra', dest='center_ra', type=float, help='RA center')
    parser.add_option('--dec', dest='center_dec', type=float,
                      help='Dec center')
    parser.add_option('--radius', dest='radius', type=float,
                      help='Search radius around RA,Dec center')
    parser.add_option('--downsample', dest='downsample_factor', type=int,
                      help='Downsample image by this factor')
    parser.add_option('--parity', dest='parity', choices=('0', '1'),
                      help='Parity (flip) of image')
    parser.add_option('--tweak-order', dest='tweak_order', type=int,
                      help='SIP distortion order (default: 2)')
    parser.add_option('--crpix-center', dest='crpix_center',
                      action='store_true', default=None,
                      help='Set reference point to center of image?')
    parser.add_option('--sdss', dest='sdss_wcs', nargs=2,
                      help='Plot SDSS image for the given WCS file; write ' +
                      'plot to given PNG filename')
    parser.add_option('--galex', dest='galex_wcs', nargs=2,
                      help='Plot GALEX image for the given WCS file; write' +
                      'plot to given PNG filename')
    parser.add_option('--substatus', '-s', dest='sub_id',
                      help='Get status of a submission')
    parser.add_option('--jobstatus', '-j', dest='job_id',
                      help='Get status of a job')
    parser.add_option('--jobs', '-J', dest='myjobs', action='store_true',
                      help='Get all my jobs')
    parser.add_option('--jobsbyexacttag', '-T', dest='jobs_by_exact_tag',
                      help='Get a list of jobs associated with a given' +
                      'tag--exact match')
    parser.add_option('--jobsbytag', '-t', dest='jobs_by_tag',
                      help='Get a list of jobs associated with a given tag')
    parser.add_option('--private', '-p', dest='public', action='store_const',
                      const='n', default='y',
                      help='Hide this submission from other users')
    parser.add_option('--allow_mod_sa', '-m', dest='allow_mod',
                      action='store_const', const='sa', default='d',
                      help='Select license to allow derivative works of ' +
                      'submission, but only if shared under same conditions ' +
                      'of original license')
    parser.add_option('--no_mod', '-M', dest='allow_mod', action='store_const',
                      const='n', default='d',
                      help='Select license to disallow derivative works of ' +
                      'submission')
    parser.add_option('--no_commercial', '-c', dest='allow_commercial',
                      action='store_const', const='n', default='d',
                      help='Select license to disallow commercial use of' +
                      ' submission')
    # load opt with defaults, as above
    opt, args = parser.parse_args()
    # add given arguments
    opt.wcs = wcsfn
    opt.apikey = ankey
    opt.upload = filename
    if ppa.havescale and ppa.restrict_scale.get() == 1:
        opt.scale_units = 'arcsecperpix'
        opt.scale_est = ('%.2f' % ppa.scale)
        opt.scale_err = 5
    # DEBUG print opt
    print('with estimated scale', opt.scale_est)
    client = NovaClient(apiurl=opt.server)
    try:
        client.login(opt.apikey)
    except RequestError:
        ppa.stat_bar("Couldn't log on to nova.astrometry.net - Check the API key")
        return

    if opt.upload or opt.upload_url:
        if opt.wcs or opt.kmz:
            opt.wait = True
        kwargs = dict()
        if opt.scale_lower and opt.scale_upper:
            kwargs.update(scale_lower=opt.scale_lower,
                          scale_upper=opt.scale_upper,
                          scale_type='ul')
        elif opt.scale_est and opt.scale_err:
            kwargs.update(scale_est=opt.scale_est,
                          scale_err=opt.scale_err,
                          scale_type='ev')
        elif opt.scale_lower or opt.scale_upper:
            kwargs.update(scale_type='ul')
            if opt.scale_lower:
                kwargs.update(scale_lower=opt.scale_lower)
            if opt.scale_upper:
                kwargs.update(scale_upper=opt.scale_upper)

        for key in ['scale_units', 'center_ra', 'center_dec', 'radius',
                    'downsample_factor', 'tweak_order', 'crpix_center', ]:
            if getattr(opt, key) is not None:
                kwargs[key] = getattr(opt, key)
        if opt.parity is not None:
            kwargs.update(parity=int(opt.parity))
        if opt.upload:
            upres = client.upload(opt.upload, **kwargs)
        stat = upres['status']
        if stat != 'success':
            print('Upload failed: status', stat)
            print(upres)
            sys.exit(-1)
        opt.sub_id = upres['subid']
    if opt.wait:
        if opt.job_id is None:
            if opt.sub_id is None:
                print("Can't --wait without a submission id or job id!")
                sys.exit(-1)
            while True:
                stat = client.sub_status(opt.sub_id, justdict=True)
                # print 'Got status:', stat
                jobs = stat.get('jobs', [])
                if len(jobs):
                    # Find the first elem in jobs that is not None  # TODO: Cleanup
                    for j in jobs:
                        if j is not None:
                            break
                    if j is not None:
                        print('Selecting job id', j)
                        opt.job_id = j
                        break
                time.sleep(5)
        success = False
        while True:
            stat = client.job_status(opt.job_id, justdict=True)
            # print 'Got job status:', stat
            # TODO : stat may be None! should recover
            if stat.get('status', '') in ['success']:
                success = (stat['status'] == 'success')
                break
            time.sleep(5)
        if success:
            client.job_status(opt.job_id)
            retrieveurls = []
            if opt.wcs:
                # We don't need the API for this, just construct URL
                url = opt.server.replace('/api/', '/wcs_file/%i' % opt.job_id)
                retrieveurls.append((url, opt.wcs))
            for url, fne in retrieveurls:
                print('Retrieving file from', url)
                fle = urlopen(url)
                txt = fle.read()
                wfl = open(fne, 'wb')
                wfl.write(txt)
                wfl.close()
                print('Wrote to', fne)
                print('nova solve time ' + str(time.time() - t_start))
                print('___________________________________________________________')
        opt.job_id = None
        opt.sub_id = None
    if opt.sub_id:
        print(client.sub_status(opt.sub_id))
    if opt.job_id:
        print(client.job_status(opt.job_id))
    if opt.jobs_by_tag:
        tag = opt.jobs_by_tag
        print(client.jobs_by_tag(tag, None))
    if opt.jobs_by_exact_tag:
        tag = opt.jobs_by_exact_tag
        print(client.jobs_by_tag(tag, 'yes'))
    if opt.myjobs:
        jobs = client.myjobs()
        print(jobs)


def nova_img2wcs(nova_key, filename, wcsfn, scale: float = None):
    '''
    Plate solves one image
    '''
    import time
    t_start = time.time()
    # import optparse
    # parser = optparse.OptionParser()
    # parser.add_option('--server', dest='server',
    #                   default=NovaClient.default_url,
    #                   help='Set server base URL (eg, %default)')
    # parser.add_option('--apikey', '-k', dest='apikey',
    #                   help='API key for Astrometry.net web service; if not' +
    #                   'given will check AN_API_KEY environment variable')
    # parser.add_option('--upload', '-u', dest='upload', help='Upload a file')
    # parser.add_option('--wait', '-w', dest='wait', action='store_true',
    #                   help='After submitting, monitor job status')
    # parser.add_option('--wcs', dest='wcs',
    #                   help='Download resulting wcs.fits file, saving to ' +
    #                   'given filename; implies --wait if --urlupload or' +
    #                   '--upload')
    # parser.add_option('--kmz', dest='kmz',
    #                   help='Download resulting kmz file, saving to given ' +
    #                   'filename; implies --wait if --urlupload or --upload')
    # parser.add_option('--urlupload', '-U', dest='upload_url',
    #                   help='Upload a file at specified url')
    # parser.add_option('--scale-units', dest='scale_units',
    #                   choices=('arcsecperpix', 'arcminwidth', 'degwidth',
    #                            'focalmm'),
    #                   help='Units for scale estimate')
    # parser.add_option('--scale-lower', dest='scale_lower', type=float,
    #                   help='Scale lower-bound')
    # parser.add_option('--scale-upper', dest='scale_upper', type=float,
    #                   help='Scale upper-bound')
    # parser.add_option('--scale-est', dest='scale_est', type=float,
    #                   help='Scale estimate')
    # parser.add_option('--scale-err', dest='scale_err', type=float,
    #                   help='Scale estimate error (in PERCENT), eg "10" if' +
    #                   'you estimate can be off by 10%')
    # parser.add_option('--ra', dest='center_ra', type=float, help='RA center')
    # parser.add_option('--dec', dest='center_dec', type=float,
    #                   help='Dec center')
    # parser.add_option('--radius', dest='radius', type=float,
    #                   help='Search radius around RA,Dec center')
    # parser.add_option('--downsample', dest='downsample_factor', type=int,
    #                   help='Downsample image by this factor')
    # parser.add_option('--parity', dest='parity', choices=('0', '1'),
    #                   help='Parity (flip) of image')
    # parser.add_option('--tweak-order', dest='tweak_order', type=int,
    #                   help='SIP distortion order (default: 2)')
    # parser.add_option('--crpix-center', dest='crpix_center',
    #                   action='store_true', default=None,
    #                   help='Set reference point to center of image?')
    # parser.add_option('--sdss', dest='sdss_wcs', nargs=2,
    #                   help='Plot SDSS image for the given WCS file; write ' +
    #                   'plot to given PNG filename')
    # parser.add_option('--galex', dest='galex_wcs', nargs=2,
    #                   help='Plot GALEX image for the given WCS file; write' +
    #                   'plot to given PNG filename')
    # parser.add_option('--substatus', '-s', dest='sub_id',
    #                   help='Get status of a submission')
    # parser.add_option('--jobstatus', '-j', dest='job_id',
    #                   help='Get status of a job')
    # parser.add_option('--jobs', '-J', dest='myjobs', action='store_true',
    #                   help='Get all my jobs')
    # parser.add_option('--jobsbyexacttag', '-T', dest='jobs_by_exact_tag',
    #                   help='Get a list of jobs associated with a given' +
    #                   'tag--exact match')
    # parser.add_option('--jobsbytag', '-t', dest='jobs_by_tag',
    #                   help='Get a list of jobs associated with a given tag')
    # parser.add_option('--private', '-p', dest='public', action='store_const',
    #                   const='n', default='y',
    #                   help='Hide this submission from other users')
    # parser.add_option('--allow_mod_sa', '-m', dest='allow_mod',
    #                   action='store_const', const='sa', default='d',
    #                   help='Select license to allow derivative works of ' +
    #                   'submission, but only if shared under same conditions ' +
    #                   'of original license')
    # parser.add_option('--no_mod', '-M', dest='allow_mod', action='store_const',
    #                   const='n', default='d',
    #                   help='Select license to disallow derivative works of ' +
    #                   'submission')
    # parser.add_option('--no_commercial', '-c', dest='allow_commercial',
    #                   action='store_const', const='n', default='d',
    #                   help='Select license to disallow commercial use of' +
    #                   ' submission')

    class options:
        def __init__(self):
            self.server = NovaClient.default_url
            self.apikey = None
            self.upload = None
            self.wait = None
            self.wcd = None
            self.kmz = None
            self.upload_url = None
            self.scale_units = None
            self.scale_lower = None
            self.scale_upper = None
            self.scale_est = None
            self.scale_err = None
            self.center_ra = None
            self.center_dec = None
            self.radius = None
            self.downsample_factor = None
            self.parity = None  # (1 or 2)
            self.tweak_order = None  # Says default 2 but we don't set a default
            self.crpix_center = None
            self.sdss_wcs = None
            self.galex_wcs = None
            self.sub_id = None   # Do these really need to be options
            self.job_id = None
            self.myjobs = True
            self.jobs_by_exact_tag = None
            self.jobs_by_tag = None
            self.public = 'n'  # y for yes, n for no
            self.allow_mod = 'n'
            self.allow_commercial = 'n'

    opt = options()
    # add given arguments
    opt.wcs = wcsfn
    opt.apikey = nova_key
    opt.upload = filename

    if scale is not None:  # and config.restrict_scale.get() == 1:
        opt.scale_units = 'arcsecperpix'
        opt.scale_est = ('%.2f' % scale)
        opt.scale_err = 5
    # DEBUG print opt
    print('with estimated scale', opt.scale_est)
    client = NovaClient(apiurl=opt.server)
    try:
        client.login(opt.apikey)
    except RequestError as e:
        print("Couldn't log on to nova.astrometry.net - Check the API key")
        raise e

    if opt.upload or opt.upload_url:
        if opt.wcs or opt.kmz:
            opt.wait = True
        kwargs = dict()
        if opt.scale_lower and opt.scale_upper:
            kwargs.update(scale_lower=opt.scale_lower,
                          scale_upper=opt.scale_upper,
                          scale_type='ul')
        elif opt.scale_est and opt.scale_err:
            kwargs.update(scale_est=opt.scale_est,
                          scale_err=opt.scale_err,
                          scale_type='ev')
        elif opt.scale_lower or opt.scale_upper:
            kwargs.update(scale_type='ul')
            if opt.scale_lower:
                kwargs.update(scale_lower=opt.scale_lower)
            if opt.scale_upper:
                kwargs.update(scale_upper=opt.scale_upper)

        for key in ['scale_units', 'center_ra', 'center_dec', 'radius',
                    'downsample_factor', 'tweak_order', 'crpix_center', ]:
            if getattr(opt, key) is not None:
                kwargs[key] = getattr(opt, key)
        if opt.parity is not None:
            kwargs.update(parity=int(opt.parity))
        if opt.upload:
            upres = client.upload(opt.upload, **kwargs)
        stat = upres['status']
        if stat != 'success':
            print('Upload failed: status', stat)
            print(upres)
            sys.exit(-1)
        opt.sub_id = upres['subid']
    if opt.wait:
        if opt.job_id is None:
            if opt.sub_id is None:
                print("Can't --wait without a submission id or job id!")
                sys.exit(-1)
            while True:
                stat = client.sub_status(opt.sub_id, justdict=True)
                # print 'Got status:', stat
                jobs = stat.get('jobs', [])
                if len(jobs):
                    # Find the first elem in jobs that is not None  # TODO: Cleanup
                    for j in jobs:
                        if j is not None:
                            break
                    if j is not None:
                        print('Selecting job id', j)
                        opt.job_id = j
                        break
                time.sleep(5)
        success = False
        while True:
            stat = client.job_status(opt.job_id, justdict=True)
            # print 'Got job status:', stat
            # TODO : stat may be None! should recover
            if stat.get('status', '') in ['success']:
                success = (stat['status'] == 'success')
                break
            time.sleep(5)
        if success:
            client.job_status(opt.job_id)
            retrieveurls = []
            if opt.wcs:
                # We don't need the API for this, just construct URL
                url = opt.server.replace('/api/', '/wcs_file/%i' % opt.job_id)
                retrieveurls.append((url, opt.wcs))
            for url, fne in retrieveurls:
                print('Retrieving file from', url)
                fle = urlopen(url)
                txt = fle.read()
                wfl = open(fne, 'wb')
                wfl.write(txt)
                wfl.close()
                print('Wrote to', fne)
                print('nova solve time ' + str(time.time() - t_start))
                print('___________________________________________________________')
        opt.job_id = None
        opt.sub_id = None
    if opt.sub_id:
        print(client.sub_status(opt.sub_id))
    if opt.job_id:
        print(client.job_status(opt.job_id))
    if opt.jobs_by_tag:
        tag = opt.jobs_by_tag
        print(client.jobs_by_tag(tag, None))
    if opt.jobs_by_exact_tag:
        tag = opt.jobs_by_exact_tag
        print(client.jobs_by_tag(tag, 'yes'))
    if opt.myjobs:
        jobs = client.myjobs()
        print(jobs)
