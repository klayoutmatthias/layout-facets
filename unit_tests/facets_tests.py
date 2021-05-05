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

import unittest
from facets import *

# Try to import both from klayout.db (PyPI klayout module) or
# pya (inside KLayout)
try:
  from klayout.db import Region, Box, Polygon, Layout, CellInstArray, Trans
except ImportError:
  from pya import Region, Box, Polygon, Layout, CellInstArray, Trans


class TestFacets(unittest.TestCase):

  def test_basic1(self):

    r1 = Region(Box(0, 0, 100, 200))
    r2 = Region(Box(-200, -100, 200, 300))
    self.assertNotEqual(hash_of_region(r1), 0)
    self.assertNotEqual(hash_of_region(r1), hash_of_region(r2))

  def test_facet(self):

    r1 = Polygon(Box(0, 0, 100, 200))
    r2 = Region(Box(-200, -100, 200, 300))
    f = Facet(r1, r1, [ r2 ])
    v1 = f.normalize()

    r1.move(10, 20)
    r2.move(10, 20)
    ff = Facet(r1, r1, [ r2 ])

    self.assertNotEqual(f.__hash__(), ff.__hash__())
    self.assertEqual(f.__eq__(ff), False)
    self.assertEqual(ff.__eq__(f), False)
    self.assertEqual(f.__ne__(ff), True)
    self.assertEqual(ff.__ne__(f), True)

    v2 = ff.normalize()

    self.assertEqual(str(v1), "0,0")
    self.assertEqual(str(v2), "10,20")
    self.assertEqual(f.__hash__(), ff.__hash__())
    self.assertEqual(f.__eq__(ff), True)
    self.assertEqual(ff.__eq__(f), True)
    self.assertEqual(f.__ne__(ff), False)
    self.assertEqual(ff.__ne__(f), False)

  def test_separator(self):

    ly = Layout()
    top_cell = ly.create_cell("TOP")
    child_cell = ly.create_cell("CHILD")

    l1 = ly.layer()
    l2 = ly.layer()
    child_cell.shapes(l1).insert(Box(100, 100, 900, 900))
    child_cell.shapes(l2).insert(Box(0, 0, 1000, 1000))

    top_cell.insert(CellInstArray(child_cell.cell_index(), Trans(100, 200)))
    top_cell.insert(CellInstArray(child_cell.cell_index(), Trans(-1100, 100)))
    top_cell.shapes(l1).insert(Box(-1000, -1000, 0, 0))

    sep = Separator(ly, cell = top_cell, seed_layer = l1, side_layers = [ l2 ], halo = 200)

    seeds = [ Box(0, 0, 800, 800), Box(0, 0, 1000, 1000) ]

    s = {}
    for f in sep.facets.keys():
      s[f.seed.bbox()] = sep.facets[f] 

    self.assertEqual(len(s), 2)
    self.assertEqual(Box(0, 0, 800, 800) in s, True)
    self.assertEqual(Box(0, 0, 1000, 1000) in s, True)
    self.assertEqual(";".join([ str(v) for v in s[Box(0, 0, 800, 800)] ]), "-1000,200;200,300")
    self.assertEqual(";".join([ str(v) for v in s[Box(0, 0, 1000, 1000)] ]), "-1000,-1000")


if __name__ == '__main__':
  unittest.main()

