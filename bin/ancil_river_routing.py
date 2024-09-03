#!/usr/bin/env python
# (C) Crown Copyright, Met Office. All rights reserved.
#
# This file is part of ANTS and is released under the BSD 3-Clause license.
# See LICENSE.txt in the root of the repository for full licensing details.
"""
River routing application
*************************

Derive the river routing sequence and direction ancillaries.

The following steps are taken:

* Landcover fraction field (LCF) is regridded to the river routing field
  using an area weighted regrid.
* Regridded LCF is used to identify points which are ocean and those which
  are also surrounded by ocean.
* At points that are entirely ocean and whose neighbours are entirely
  ocean, the river direction and sequence is set to missing data.
* At points that are entirely ocean, but whose neighbours are not entirely
  ocean, the river direction is set to 9, to signify a pour point into the
  ocean.
* On output of ancillary, the UM grid definition is inherited from the
  input LCF, as there is a detachment between the river routing field and
  the UM grid definition.

"""
import ants
import ants.config
import ants.decomposition as decomp
import ants.utils
import iris
import numpy as np

POUR_POINT_INDICATOR = 9


def load_data(source, land_cover_fraction):
    sequence_cube, direction_cube = ants.load_cubes(
        source, ["river_routing_sequence", "river_routing_direction"]
    )
    lcf_cube = ants.load_cube(land_cover_fraction, "land_area_fraction")

    return sequence_cube, direction_cube, lcf_cube


def river_routing(sequence_cube, direction_cube, land_cover_fraction_cube):
    # Regrid the land cover fraction to the river trip routing source grid.
    lcf_cube = decomp.decompose(
        ants.analysis.mean, land_cover_fraction_cube, direction_cube
    )

    neighbours = ants.analysis.MooreNeighbourhood(lcf_cube)
    ocean_indicator = 0
    sea_only = lcf_cube.data == ocean_indicator
    sea_only_neighbours = neighbours.all_equal_value(ocean_indicator)

    # Set pour point where its next to the coast.
    direction_cube.data[sea_only] = POUR_POINT_INDICATOR
    # Mask direction where points AND their neighbours are ocean.
    mask = sea_only_neighbours * sea_only
    for cube in [direction_cube, sequence_cube]:
        cube.data = np.ma.array(cube.data, copy=False)
        cube.data[mask] = np.ma.masked

    return sequence_cube, direction_cube


def main(source_filepath, land_cover_fraction_filepath, output_filepath):
    sequence_cube, direction_cube, lcf_cube = load_data(
        source_filepath, land_cover_fraction_filepath
    )
    sequence_cube, direction_cube = river_routing(
        sequence_cube, direction_cube, lcf_cube
    )
    # Write the output
    ants.save(iris.cube.CubeList([direction_cube, sequence_cube]), output_filepath)
    return sequence_cube, direction_cube


def _get_parser():
    parser = ants.AntsArgParser()
    parser.add_argument(
        "--land-cover-fraction", type=str, help="Land cover fraction.", required=True
    )
    return parser


if __name__ == "__main__":
    args = _get_parser().parse_args()

    main(args.sources, args.land_cover_fraction, args.output)
