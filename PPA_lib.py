import os
import platformdirs
from tkinter import StringVar, IntVar, DoubleVar  # Replace with non-tkinter types


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
