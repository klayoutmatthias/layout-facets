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

  """
  Helper function to compute the hash value of a region 
  (should be part of KLayout API)
  """

  h = 0
  for p in region.each():
    h = hash((h, p.hash()))
  return h


def compare_region(region1, region2):

  """
  Helper function to compare two regions for equality
  (should also be part of KLayout API)
  """

  p1 = set([ p for p in region1.each() ])
  p2 = set([ p for p in region2.each() ])
  return p1 == p2


class Facet(object):

  """
  An representing a single facet

  Attributes are:
    * seed: the seed polygon
    * mask: the seed polygon oversized by the halo
    * side_regions: one Region object per side layer containing the clipped side layer polygons
    * result: a generic attribute by which the operator can attach results for the integrator
  """

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

  """
  The central class of the facets framework
  """

  def __init__(self, layout, seed_layer, cell = None, merge = True, side_layers = [], halo = 0):

    """
    Constructor

    Creates a facet representation from the given layout.

    "cell" is the top cell to start with. If not given, the exisiting top cell is used
    (which must be unique then).

    "seed_layer": a KLayout layer index (NOT the GDS number) for the layer from which
    to take the seeds.

    "side_layers": an array of layer indexes (NOT the GDS numbers) for the side layers.

    "halo": the halo distance in database units of the layout.

    "merge" indicates if the polygons on the seed layer are merged before being used
    as seeds (default: yes).
    """

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

    """
    Performs the processing step
    """

    for f in self.facets.keys():
      operator.do(f)

  def integrate(self, integrator):
    
    """
    Performs the integration step
    """

    for f in self.facets.keys():
      integrator.integrate(f, self.facets[f])


class Operator(object):

  """
  A template for the operator object
  The "do" method will be presented all facets, but each facet once.
  """

  def do(self, facet):
    pass


class Integrator(object):

  """
  A template for the integrator object
  The "integrate" method will be calls with every facet and a list with the original locations.
  """

  def integrate(self, facet, offsets):
    pass

