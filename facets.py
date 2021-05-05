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

# Try to import both from klayout.db (PyPI klayout module) or
# pya (inside KLayout)
try:
  from klayout.db import Region, RecursiveShapeIterator
except ImportError:
  from pya import Region, RecursiveShapeIterator


def hash_of_region(region):
  h = 0
  for p in region.each():
    h = hash((h, p.hash()))
  return h


def compare_region(region1, region2):
  p1 = set([ p for p in region1.each() ])
  p2 = set([ p for p in region2.each() ])
  return p1 == p2


class Facet(object):

  def __init__(self, mask, seed, side_regions):
    
    self.mask = mask.dup()
    self.seed = seed.dup()
    self.side_regions = [ r.dup() for r in side_regions ]
    self.result = None

  def normalize(self):

    v = self.seed.bbox().p1
    self.seed.move(-v) 
    self.mask.move(-v) 
    for s in self.side_regions:
      s.move(-v)
    return v

  def __hash__(self):

    h = self.seed.hash()
    for r in self.side_regions:
      h = hash((h, hash_of_region(r)))
    return h
    
  def __eq__(self, other):

    if self.seed != other.seed:
      return False
    if len(self.side_regions) != len(other.side_regions):
      return False
    for n in range(0, len(self.side_regions)):
      if not compare_region(self.side_regions[n], other.side_regions[n]):
        return False
    return True

  def __ne__(self, other):

    return not self.__eq__(other)


class Separator(object):

  def __init__(self, layout, seed_layer, cell = None, merge = True, side_layers = [], halo = 0):

    self.facets = {}

    if not cell:
      cell = layout.top_cell()

    seed_region = Region(cell.begin_shapes_rec(seed_layer))
    if merge:
      seed_region.merge()

    for seed in seed_region.each(): 

      mask = Region(seed)
      if halo > 0:
        mask.size(halo)

      side_regions = []
      for sl in side_layers:
        touching_halo = Region(RecursiveShapeIterator(layout, cell, sl, Region(seed), False))
        side_regions.append(touching_halo & mask)

      facet = Facet(mask, seed, side_regions)
      v = facet.normalize()

      if facet in self.facets:
        self.facets[facet].append(v)
      else:
        self.facets[facet] = [v]

  def process(self, operator):

    for f in self.facets.keys():
      operator.do(f)

  def integrate(self, integrator):
    
    for f in self.facets.keys():
      integrator.integrate(f, self.facets[f])


class Operator(object):
  def do(self, facet):
    pass


class Integrator(object):
  def integrate(self, facet, offsets):
    pass

