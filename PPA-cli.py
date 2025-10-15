import os
import argparse
import PPA_lib
from astropy.io import fits

argParser = argparse.ArgumentParser(description="A python utility to help align any equotorial telescope by imaging the celestial pole region")

argParser.add_argument("--solver", type=str, nargs="?", default=None, help="Whether to use online \"nova\" or \"local\" solver", required=True)
argParser.add_argument("--horizontal", type=str, nargs="?", metavar="horizontal_file_path", default=None, help="The filepath to the horizontal image", required=True)
argParser.add_argument("--vertical", type=str, nargs="?", metavar="vertical_file_path", default=None, help="The filepath to the vertical image", required=True)
argParser.add_argument("--improved", type=str, nargs="?", metavar="improved_file_path", default=None, help="The filepath to the improved image after adjusting scope mount")

argParser.add_argument("--cache-dir", type=str, nargs="?", default=PPA_lib.get_cache_file_path(), help="Filepath to look in for cached .wcs files")
argParser.add_argument("--config", type=str, nargs="?", default=PPA_lib.get_config_file_path(), help="Filepath to config to use")
argParser.add_argument("--more-data", type=bool, nargs="?", default=False, help="Returns more detailed information")

args = argParser.parse_args()

solver_options = ["local", "nova"]
if args.solver not in solver_options:
    print("Option '--solver' must be one of " + str(solver_options))
    exit(2)

"""
Verify provided images exist or their WCS version in cache dir exists
Verify config exists
Load config
Plate solve images without wcs
Find error
Return results
"""
print(args)

config_file_path = args.config
cache_dir = args.cache_dir
return_more_data = args.more_data
solver = args.solver


###
# TODO:
# Get config params
#    Separate config from PPA obj
# Use local vs nova
# Provide the "more" data output


config = PPA_lib.PPAConfig()


def solve_img(imagePath):
    PPA_lib.plate_solve(config, imagePath, solver, cache_dir=cache_dir)


hImgPath = args.horizontal
hWcsPath = PPA_lib.get_wcs_file_path(hImgPath, cache_dir)
solve_img(hImgPath)
hdulist_h = fits.open(hWcsPath)

vImgPath = args.vertical
vWcsPath = PPA_lib.get_wcs_file_path(vImgPath, cache_dir)
solve_img(vImgPath)
hdulist_v = fits.open(vWcsPath)

iImgPath = args.improved
iWcsPath = None
hdulist_i = None
if iImgPath is not None:
    iWcsPath = PPA_lib.get_wcs_file_path(iImgPath, cache_dir)
    solve_img(iImgPath)
    hdulist_i = fits.open(iWcsPath)

axis = PPA_lib.find_ra_axis_pix_coords(hdulist_v[0], hdulist_h[0])
# Have the wcs files, just get the error
if hdulist_i is None:
    error = PPA_lib.find_error(axis, hdulist_h)
else:
    error = PPA_lib.find_error(axis, hdulist_i)


def formatError(err):
    print(err)
    if err[0] > 0:
        inst = 'Right '
    else:
        inst = 'Left '
    decdeg = abs(err[0])
    inst = inst + ('%02d:%02d:%02d' % PPA_lib.decdeg2dms(decdeg))

    if err[1] > 0:
        inst = inst + ' Down '
    else:
        inst = inst + ' Up '
    decdeg = abs(err[1])
    inst = inst + ('%02d:%02d:%02d' % PPA_lib.decdeg2dms(decdeg))
    return inst


print(formatError(error))

exit(1)












# ppa-cli --horizontal /path/to/horiz/image --verticle /path/horiz/image --[local|nova]
# Returns > left: 6.156705  down: 21.456830

# ppa-cli --horizontal-wcs /path/to/horiz/wcs --verticle-wcs /path/verticle/wcs --improvement /path/improvement/image
# Returns > left: 0.856705  up: 1.456830

# --horizontal will look in cache dir for wcs, --horizontal-wcs will use provided path to wcs
# Or a --cache-dir instead of wcs option
# --config

# ppa-cli --horizontal /path/to/horiz/wcs --verticle /path/verticle/wcs --improvement /path/improvement/image --config /config.ini


# --more-data will return
"""
{
    hemi: 'n',
    scale: 1.6
    error: {
        left: 0.856705,
        up: 1.456830,
    }
    celestial-pole: {
        ra: 90,
        dec: 0,
        alt: x,
        az: y
    },
    axis: {
        ra: 90.856705,
        dec: -1.456830
        alt: x,
        az: y
    },
    stars: [
        {
            star: "Polaris",
            ra: 91,
            dec: 3
        },
        {
            star: "Lambda",
            ra: 91,
            dec: 3
        },
    ]
}
"""
