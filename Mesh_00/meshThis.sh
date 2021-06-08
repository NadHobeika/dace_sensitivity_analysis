#!/bin/bash

## Generate the domain around buldings
surfaceGenerateBoundingBox constant/triSurface/merge.stl boundBox.stl 30 0 0 0 0 75
#
# Change to .fms
surfaceFeatureEdges boundBox.stl merge.fms  -angle 20 

# Start meshing
cartesianMesh | tee log.cartesianMesh

# Improve mesh quality
improveMeshQuality -nIterations 100 -nSurfaceIterations 10 | tee log.improveMeshQuality

# Renumber mesh
renumberMesh -overwrite | tee log.renumberMesh 

# Check mesh
#checkMesh -constant | tee log.checkMesh
