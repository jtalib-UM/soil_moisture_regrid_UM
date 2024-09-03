#!/usr/bin/env python
# (C) Crown Copyright, Met Office. All rights reserved.
#
# This file is part of ANTS and is released under the BSD 3-Clause license.
# See LICENSE.txt in the root of the repository for full licensing details.
"""
Ancillary fill and merge application
************************************

The purpose of this application is to fill missing data, resolve differences
between coastlines with an optionally supplied landseamask and merge datasets.

When two sources are provided, a merge is performed, where the first is
considered the primary while the second is the alternate which is merged into
the primary.  See :func:`ants.analysis.merge` for further details.  In the case
of multiple phenomena within two source files, primary and alternate cubes are
sorted to ensure that the correct phenomena are paired for merging
(see :func:`ants.utils.cube.group_cubes`).
Filling of missing data is perfomed as a final step which can optionally
account for a landseamask.

"""
import ants
import cartopy
from ants.utils.cube import create_time_constrained_cubes


def load_data(
    primary_source,
    alternate_source=None,
    validity_polygon_filepath=None,
    target_mask_filepath=None,
    land_fraction_threshold=None,
    begin=None,
    end=None,
):
    """
    Load the necessary data for performing a merge and fill operation.

    Parameters
    ----------
    primary_source : str
        Primary source filepath.
    alternate_source : str, optional
        Alternate source filepath used when merging.
    validity_polygon_filepath : str, optional
        Filepath to the validity polygon which represents the data from the
        primary dataset which is valid.
    target_mask_filepath : str, optional
        Filepath to the target field mask.
    land_fraction_threshold : str, optional
    begin: datetime, optional
        Datetime to start the processing.
    end: datetime, optional
        Datetime to end the processing.


    Returns
    -------
    : tuple
        The tuple contains the primary cube(s) (:class:`~iris.cube.CubeList`),
        alternate cube(s) (:class:`~iris.cube.CubeList`), validity polygon
        (:class:`shapely.geometry`) and target mask (:class:`~iris.cube.Cube`)
        respectively.

    """
    primary_cubes = ants.load(primary_source)
    if begin is not None:
        primary_cubes = create_time_constrained_cubes(primary_cubes, begin, end)
    alternate_cubes = None
    if alternate_source:
        alternate_cubes = ants.load(alternate_source)
        if begin is not None:
            alternate_cubes = create_time_constrained_cubes(alternate_cubes, begin, end)

    rpolygon = None
    if validity_polygon_filepath:
        rpolygon = cartopy.io.shapereader.Reader(validity_polygon_filepath)
        rpolygon = [polygon for polygon in rpolygon.geometries()]
        if len(rpolygon) > 1:
            raise RuntimeError(
                "Expecting file to contain a single geometry, "
                "{} found".format(len(rpolygon))
            )
        rpolygon = rpolygon[0]

    tgt_cube = None
    if target_mask_filepath:
        tgt_cube = ants.fileformats.load_landsea_mask(
            target_mask_filepath, land_fraction_threshold
        )
    return primary_cubes, alternate_cubes, rpolygon, tgt_cube


def main(
    primary_source,
    output,
    alternate_source=None,
    validity_polygon_filepath=None,
    target_mask_filepath=None,
    invert_mask=True,
    land_fraction_threshold=None,
    begin=None,
    end=None,
):
    """
    Perform merge and fill operation on the provided sources.

    In the case where an alternate_source is provided, a merge is taken place
    with the primary.  Filling of missing data is perfomed as a final step
    which can optionally account for a landseamask.

    Parameters
    ----------
    primary_source : str
        Primary source filepath.
    alternate_source : str, optional
        Alternate source filepath, used when merging.
    output : str
        Merged output filepath.
    validity_polygon_filepath : str, optional
        Filepath to the validity polygon which represents the data from the
        primary dataset which is valid.
    target_mask_filepath : str, optional
        Filepath to the target mask.
    invert_mask : bool, optional
       When set to True, treat target_mask True (1) values as unmasked.  When set
       to False, treat target_mask True (1) values as masked.
       This is particularly useful when considering that landseamasks are
       provided which are then inverted for land fields.
    land_fraction_threshold : str, optional
    begin : datetime, optional
        If provided, all source data prior to this year is discarded.  Default is to
        include all source data.
    end : datetime, optional
        If provided, all source data after this year is discarded.  Default is to
        include all source data.
    Returns
    -------
    : :class:`~iris.cube.CubeList`
        Merged result.

    """
    primary_cubes, alternate_cubes, validity_polygon, lbm = load_data(
        primary_source,
        alternate_source,
        validity_polygon_filepath,
        target_mask_filepath,
        land_fraction_threshold,
        begin,
        end,
    )

    result = primary_cubes
    if alternate_cubes is not None:
        result = ants.analysis.merge(primary_cubes, alternate_cubes, validity_polygon)
    if target_mask_filepath:
        ants.analysis.make_consistent_with_lsm(result, lbm, invert_mask)
    ants.save(result, output)
    return result


def _get_parser():
    parser = ants.AntsArgParser()
    lsm_help = (
        "Path to the land sea mask.  If not supplied, the missing "
        "neighbour search simply considers all points valid to choose "
        "from."
    )
    # Define these next two arguments here as this application brakes the mold
    # by them being optional, not mandatory.
    parser.add_argument("--target-lsm", type=str, help=lsm_help, required=False)
    parser.add_argument(
        "--land-threshold",
        type=float,
        required=False,
        help="Land fraction threshold for converting "
        "land fraction to a landsea mask. \n"
        "Fractions greater than this specified "
        "are masked.  Required if the field "
        "provided is a land fraction rather than "
        "land binary mask field.",
    )

    poly_help = (
        "Validity polygon filepath.  If not supplied, the entirety "
        "of the primary takes priority except in the presence of NAN "
        "values.  This is expected to be a shapefile and is read by "
        "cartopy.io.shapereader.Reader"
    )
    parser.add_argument("--polygon", type=str, help=poly_help, required=False)
    invmask_help = (
        "Invert the provided target mask or not.\n"
        "Default is True. \n"
        "This is particularly useful when dealing with land vs "
        "ocean fields, where it's common to invert the lsm to "
        "denote source ocean fields."
    )
    parser.add_argument(
        "--invert-mask", action="store_false", help=invmask_help, required=False,
    )
    return parser


if __name__ == "__main__":
    # Parse commandline arguments
    parser = _get_parser()
    args = parser.parse_args()

    try:
        source1, source2 = args.sources
    except ValueError:
        source1 = args.sources[0]
        source2 = None
    main(
        source1,
        args.output,
        source2,
        args.polygon,
        args.target_lsm,
        invert_mask=args.invert_mask,
        land_fraction_threshold=args.land_threshold,
        begin=args.begin,
        end=args.end,
    )
