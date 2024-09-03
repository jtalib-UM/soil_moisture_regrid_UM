#!/usr/bin/env python
# (C) Crown Copyright, Met Office. All rights reserved.
#
# This file is part of ANTS and is released under the BSD 3-Clause license.
# See LICENSE.txt in the root of the repository for full licensing details.
"""
General regrid application
**************************

Regrids data from a source to a target grid using
:class:`ants.regrid.GeneralRegridScheme`.  The result is written to an output
file.  The application supports both horizontal and vertical regridding.  The
regrid algorithm can be specified in the ants configuration file as described
in :class:`ants.config.GlobalConfiguration`. See :mod:`ants.regrid` and
https://code.metoffice.gov.uk/doc/ancil/ants/latest/regrid.html for further
details.

Additionally, if the `target_lsm` argument is used, the land sea mask is used
for a nearest neighbour fill of missing data for land only or ocean only
fields after the regrid has been done.

"""
import ants
import ants.decomposition as decomp
import ants.fileformats._ugrid
import ants.utils
from ants.config import CONFIG
from ants.utils.cube import create_time_constrained_cubes


def load_data(
    source,
    target_grid=None,
    target_landseamask=None,
    land_fraction_threshold=None,
    begin=None,
    end=None,
):
    source_cubes = ants.load(source)
    if begin is not None:
        source_cubes = create_time_constrained_cubes(source_cubes, begin, end)
    if target_grid:
        target_cube = ants.load_grid(target_grid)
    else:
        target_cube = ants.fileformats.load_landsea_mask(
            target_landseamask, land_fraction_threshold
        )
    return source_cubes, target_cube


def regrid(sources, target, ugrid_target=False):
    sources = ants.utils.cube.as_cubelist(sources)
    results = []
    scheme = ants.regrid.GeneralRegridScheme(horizontal_scheme=ants.regrid.rectilinear.Linear(extrapolation_mode='linear'))
    if ugrid_target:
        scheme = ants.regrid.GeneralRegridScheme(
            horizontal_scheme=ants.regrid._ugrid._UGrid()
        )
        # Current configuration of ESMPy for UGrid (i.e. Conservative
        # regridding) requires bounds.  This restriction may be relaxed later.
        ants.utils.cube.guess_horizontal_bounds(sources)
    for source in sources:
        print (source)
        print (target)
        results.append(source.regrid(target, scheme))
        print (results)
    return results


def main(
    source_path,
    output_path,
    target_path=None,
    target_lsm_path=None,
    invert_mask=True,
    land_fraction_threshold=None,
    begin=None,
    end=None,
):
    """
    General regrid application top level call function.

    Loads source data cubes, regrids them to match target data cube
    co-ordinates, and saves result to output.  In addition to writing the
    resulting data cube to disk, also returns the regridded data cube.

    Parameters
    ----------

    source_path : str
        File path for one or more files which contain the data to be
        regridded.
    target_path : str
        File path for files that provide the grid to which the source data
        cubes will be mapped.  Separate files can be provided to generate a
        complete grid i.e. a namelist for vertical levels can be used with a
        data file for the horizontal coordinates.
    target_lsm_path : str
        File path for a land sea mask that provides the grid to which
        the source data cube will be mapped.  The output will be made
        consistent with this land sea mask.
    invert_mask : bool, optional
        Determines whether to invert the mask for the `target_lsm_path`
        argument.
        When set to True, treat target_mask True (1) values as unmasked.  When set
        to False, treat target_mask True (1) values as masked.
        Defaults to True.
    output_path : str
        Output file path to write the regridded data to.
    land_fraction_threshold : str
    begin : datetime, optional
        If provided, all source data prior to this year is discarded.  Default is to
        include all source data.
    end : datetime, optional
        If provided, all source data after this year is discarded.  Default is to
        include all source data.
    Returns
    -------
    : :class:`~iris.cube.Cube`
    A single data cube with the regridded data.

    """
    source_cubes, target_cube = load_data(
        source_path, target_path, target_lsm_path, land_fraction_threshold, begin, end,
    )
    if ants.utils.cube._is_ugrid(target_cube):
        if CONFIG["ants_regridding_horizontal"]["scheme"] is not None:
            raise ValueError(
                "Invalid configuration: cannot use scheme {} for "
                "horizontal regridding with a UGrid target.".format(
                    CONFIG["ants_regridding_horizontal"]["scheme"]
                )
            )
        save = ants.fileformats._ugrid.save
        regridded_cubes = regrid(source_cubes, target_cube, ugrid_target=True)
    else:
        save = ants.save
        regridded_cubes = decomp.decompose(regrid, source_cubes, target_cube)
#    if target_lsm_path:
#        ants.analysis.make_consistent_with_lsm(
#            regridded_cubes, target_cube, invert_mask
#        )
    save(regridded_cubes, output_path)

    return regridded_cubes


def _get_parser():
    parser = ants.AntsArgParser(target_lsm=True, target_grid=True)
    invmask_help = (
        "Invert the provided target mask or not.\n"
        "Default is True. \n"
        "This is particularly useful when dealing with land vs "
        "ocean fields, where it's common to invert the lsm to "
        "denote source ocean fields.\n"
    )
    parser.add_argument(
        "--invert-mask", action="store_false", help=invmask_help, required=False,
    )
    return parser


def _run_app():
    parser = _get_parser()
    args = parser.parse_args()

    source = args.sources
    main(
        source,
        args.output,
        args.target_grid,
        args.target_lsm,
        args.invert_mask,
        args.land_threshold,
        args.begin,
        args.end,
    )


if __name__ == "__main__":
    _run_app()
