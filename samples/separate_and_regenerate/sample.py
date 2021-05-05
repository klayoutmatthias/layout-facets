
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#

# This sample will separate and generate the layout in "sample.gds" 
# along the seed polygons of layer 6/0, taking layer 3/0, 4/0 and 5/0 as 
# additional side layers. 
# 
# The layout is separated into facets and from these a new
# layout is reconstructed which must reproduce layer 6/0
# and the neighborhood on the side layers within the halo
# distance of 200nm.

import facets

# Try to import both from klayout.db (PyPI klayout module) or
# pya (inside KLayout)
try:
  from klayout.db import Layout, Text, CellInstArray, Trans
except ImportError:
  from pya import Layout, Text, CellInstArray, Trans


class SampleOperator(object):

  """
  This sample operator creates a text to label the facet with 
  an index.
  """

  def __init__(self):
    self.facet_index = 0

  def do(self, facet):

    self.facet_index += 1

    # create a text with the facet index and store in the facet's
    # generic result value
    p = facet.seed.bbox().center()
    facet.result = Text("FACET #" + str(self.facet_index), p.x, p.y)


class SampleIntegrator(object):

  def __init__(self, layout):

    self.layout = layout
    self.l3 = layout.layer(3, 0)
    self.l4 = layout.layer(4, 0)
    self.l5 = layout.layer(5, 0)
    self.l6 = layout.layer(6, 0)

    # this is where the texts go
    self.l0 = layout.layer(0, 0)

    self.top_cell = layout.create_cell("TOP")
    self.all_facets_cell = self.layout.create_cell("ALL_FACETS")
    self.facet_x = 0

  def integrate(self, facet, offsets):

    # Creates one cell per facet and places it where the original locations 
    # have been found. Copies layout, side layout and generated texts 
    # to the facet cell.
    # 
    # This code will also place all different facets into the second
    # "ALL_FACETS" top cell.

    facet_cell = self.layout.create_cell("FACET")

    facet_cell.shapes(self.l0).insert(facet.result)
    facet_cell.shapes(self.l0).insert(facet.mask)

    facet_cell.shapes(self.l6).insert(facet.seed)
    for l, i in [(self.l3, 0), (self.l4, 1), (self.l5, 2)]:
      facet_cell.shapes(l).insert(facet.side_regions[i])

    for o in offsets:
      self.top_cell.insert(CellInstArray(facet_cell.cell_index(), Trans(o.x, o.y)))

    self.all_facets_cell.insert(CellInstArray(facet_cell.cell_index(), Trans(self.facet_x, 0)))
    self.facet_x += facet.mask.bbox().width() + 200


ly = Layout()
ly.read("sample.gds")

l3 = ly.layer(3, 0)
l4 = ly.layer(4, 0)
l5 = ly.layer(5, 0)
l6 = ly.layer(6, 0)

# Note: the halo is given in layout's database units
halo = 200

# Use the separator to produce the facets
sep = facets.Separator(layout = ly, seed_layer = l6, side_layers = [ l3, l4, l5 ], halo = halo)

# Process the facets - assigns texts
sep.process(SampleOperator())

# Integrate the facets - produces the regenerated layout
regenerated = Layout()
sep.integrate(SampleIntegrator(regenerated))
regenerated.write("sample-regenerated.gds")


