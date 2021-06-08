#!/bin/bash

# transform faceCompact notation of OF Foundation to standard one by OF ESI
foamFormatConvert | tee log.foamFormatConvert

# Generate boundary layers according to meshDict
generateBoundaryLayers | tee log.generateBoundaryLayers

# Renumber mesh
renumberMesh -overwrite | tee log.renumberMesh 

# Check mesh
checkMesh -constant | tee log.checkMesh
