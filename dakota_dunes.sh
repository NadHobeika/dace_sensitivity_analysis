#!/bin/bash
#
# Description
#   Run the dakota tool and run the process chain
#
# ------------------------------------------------------------------------------


# Assign $1 and $2 to variables and reset because they seem to interferewith
# OpenFOAM's postProcess and sourcing
# ------------------------------------------------------------------------------
infile=$1
outfile=$2
set --


# Dakota change the parameters in this file
# ------------------------------------------------------------------------------
dprepro $infile system/dakotaParameter.orig system/dakotaParameter

# Run simulation with new parameter set
# ------------------------------------------------------------------------------


    # Get angle1, angle2, length of inlet + loop number
    #---------------------------------------------------------------------------
    alpha=`head -1 system/dakotaParameter | tail -1 | cut -d'=' -f2`
    beta=`head -2 system/dakotaParameter | tail -1 | cut -d'=' -f2`
    distance_dunes=`head -3 system/dakotaParameter | tail -1 | cut -d'=' -f2`
    #wind=`head -4 system/dakotaParameter | tail -1 | cut -d'=' -f2`
    wind=60
    #loopNumber=`cat .optimizationLoop`
    loopNumber=$(echo $infile | awk -F. '{print $NF}')


    # Transform the scientific notation into a readable format for | bc
    # Here we remove e or E with *10^
    #---------------------------------------------------------------------------
    alpha=`echo $alpha | sed -e 's/[eE]+*/\*10\^/'`
    beta=`echo $beta | sed -e 's/[eE]+*/\*10\^/'`
    distance_dunes=`echo $distance_dunes | sed -e 's/[eE]+*/\*10\^/'`
    wind=`echo $wind | sed -e 's/[eE]+*/\*10\^/'`


    # Optical stuff
    #---------------------------------------------------------------------------
    alpha=`echo "scale=4; $alpha" | bc`
    beta=`echo "scale=4; $beta" | bc`
    distance_dunes=`echo "scale=4; $distance_dunes" | bc`
    wind=`echo "scale=4; $wind" | bc`



    # Output the parameters that are used now
    #---------------------------------------------------------------------------
    >&2 echo -e "   ++++ Evaluate sample $loopNumber"
    >&2 echo -e "   |"
    >&2 echo -e "   |--> alpha = $alpha [degree]"
    >&2 echo -e "   |--> beta = $beta [degree]"
    >&2 echo -e "   |--> distance to dunes = $distance_dunes [m]"
    >&2 echo -e "   |--> wind direction = $wind [degree]"


    # Set the new angle parameters for the baffles
    #---------------------------------------------------------------------------
    cp system/parametricGeometryDict system/parametricGeometry
    sed "s/alpha/$alpha/" system/parametricGeometry -i
    sed "s/beta/$beta/" system/parametricGeometry -i
    sed "s/distance_dunes/$distance_dunes/" system/parametricGeometry -i
    sed "s/wind/$wind/" system/parametricGeometry -i


  # choose the type of case depending on the wind direction
  #---------------------------------------------------------------------------
  cp templatedir/initialConditions.template initialConditions.in
  cp templatedir/ABLConditions.template ABLConditions.in
  mkdir Mesh
  U=4.9
  Ucomp1=`echo "c($wind*3.14/180)*$U" | bc -l`
  Ucomp2=`echo "s($wind*3.14/180)*$U" | bc -l`
  Dcomp1=`echo "c($wind*3.14/180)" | bc -l`
  Dcomp2=`echo "s($wind*3.14/180)" | bc -l`
  if [ $(echo " $wind == 0" | bc) -eq 1 ]
  then
    cp -r Mesh_00/. Mesh/.;
  elif [ $(echo " $wind == 90" | bc) -eq 1 ]
  then
    cp -r Mesh_90/. Mesh/.;
  else
    cp -r Mesh_xx/. Mesh/.;
  fi
  sed 's/Ucomp1/'${Ucomp1}'/g' initialConditions.in > initialConditions.1
  sed 's/Ucomp2/'${Ucomp2}'/g' initialConditions.1 > initialConditions.2
  sed 's/Dcomp1/'${Dcomp1}'/g' ABLConditions.in > ABLConditions.1
  sed 's/Dcomp2/'${Dcomp2}'/g' ABLConditions.1 > ABLConditions.2
  mv initialConditions.2 initialConditions.in
  mv ABLConditions.2 ABLConditions.in
  cp -r initialConditions.in 0/include/initialConditions
  cp -r ABLConditions.in 0/include/ABLConditions
  rm initialConditions.1 initialConditions.in
  rm ABLConditions.1 ABLConditions.in


  # Make loop folder for log files
  #---------------------------------------------------------------------------
  logFolder_="Log/Optimization"$loopNumber
  mkdir -p $logFolder_


  # Save dprepro output file because postProcessing in OpenFOAM overrides $2
  #---------------------------------------------------------------------------
  #outfile="$2"


  # Prepare for OpenFOAM: set geometry and clean
  #---------------------------------------------------------------------------
  rm -rf constant/polyMesh
  >&2 echo "   |--> Alter geometry"
  source system/parametricGeometry >> log.geometry


  # Run the simulation
  #---------------------------------------------------------------------------
  >&2 echo "   |--> Start simulation"
  #source runOpenFoamTest > $logFolder_/solving
  >&2 echo "   |--> Create mesh"
  cd Mesh
  source /opt/OpenFOAM/openfoam-esi-dev/etc/bashrc
  ln -s ../constant .
  source meshThis.sh
  cd ..
  touch test_02_degree_00.foam

  #------------------------------------------------------------------------------
  >&2 echo "   |--> simpleFoam"
  source /opt/OpenFOAM/OpenFOAM-8/etc/bashrc
  decomposePar -copyZero
  mpirun -np 20 simpleFoam -parallel >& log.SF
  #wait

  #------------------------------------------------------------------------------
  >&2 echo "   |--> Reconstruct case"
  reconstructParMesh -constant
  reconstructPar -latestTime

  #------------------------------------------------------------------------------
  >&2 echo "   |--> Sample fields"
  simpleFoam -postProcess -func sample1
  simpleFoam -postProcess -func sample2
  #simpleFoam -postProcess -func sample3
  >&2 echo "   |--> End simulation"


  # Average velocity
  #---------------------------------------------------------------------------
  last_time=$(ls -1 | sort -n | tail -n 1)
  input1="postProcessing/sample1/$last_time/somePoints_U.xy"
  input2="postProcessing/sample2/$last_time/somePoints_U.xy"
  #input="postProcessing/sample/10/somePoints_U.xy"
  #Uaverage=0
  #it=0
  #>&2 echo "   |--> HERE 1"
  #while IFS= read -r line
  #do
#	  Ux=`echo $line | awk '{print $4}'`
#	  Uy=`echo $line | awk '{print $5}'`
#	  Uz=`echo $line | awk '{print $6}'`
#	  tempUx=`echo "e(2*l($Ux))" | bc -l`
#	  tempUy=`echo "e(2*l($Uy))" | bc -l`
#	  tempUz=`echo "e(2*l($Uz))" | bc -l`
#	  sum_dir=`echo "$tempUx + $tempUy + $tempUz" | bc -l`
#	  mag_U=$(echo "scale=2;sqrt($sum_dir)" | bc -l)
#	  Uaverage=$(echo "$Uaverage + $mag_U" | bc -l)
#	  it=$((it+1))
 # done < "$input"
  #>&2 echo "   |--> HERE 2"
  #>&2 echo "   |--> $Uaverage"
  #>&2 echo "   |--> $it"
  #Uaverage=$(echo "$Uaverage / $it" | bc -l)
  sediment=($(python3 getTransportRate.py $input1 $input2 $wind))
  >&2 echo "   |--> $sediment"
  echo "$sediment" > sediment
  
  
  # Prepare results (this may not work in all environments)
  # What I do is simply to copy the mesh and the results into a new time
  # folder that we can check out the simple calculations
  #--------------------------------------------------------------------------
  #mkdir results/$loopNumber
  #cp -r constant/polyMesh results/$loopNumber
  #cp -r $last_time/* results/$loopNumber


  # Remove time directorys (reg expression would be nicer) and mesh
  #---------------------------------------------------------------------------
  #rm -rf 1* 2* 4* 5* 6* 7* 8* 9* constant/polyMesh 
  #rm -rf 0/include/ABLConditions 0/include/initialConditions
  # rm system/blockMeshDict
  rm -rf system/dakotaParameter
  rm -rf processor*


  # Resonse function:
  #   1:  the mean temperature should be achieved
  #   2:  the temperature distribution should be as good as possible
  # Both could be minimized (not done here)
  #---------------------------------------------------------------------------
  #funct1=`echo "scale=6; $Uaverage" | bc`
  #funct2=`echo "scale=6; $Tmax-$Tmin" | bc`

  #if [ `echo $funct1 | grep "-"` ];
  #then
  #    funct1=${funct1//-}
  #fi

  #if [ `echo $funct2 | grep "-"` ];
  #then
  #    funct2=${funct2//-}
  #fi


  >&2 echo "   |--> Sedimentation is: $sediment"
  >&2 echo "   |"
  #echo -e "$angle1\t$angle2\t$length\t$funct1\t$funct2" >> analyseData.dat
  echo -e "$sediment" > .dakotaInput.dak


  # Increase the loop number and store in dummy file
  #--------------------------------------------------------------------------
  echo $((loopNumber+1)) > .optimizationLoop


# Generate ouput file for DAKOTA's algorithm (Object function)
#------------------------------------------------------------------------------
cp .dakotaInput.dak $outfile

sleep 2.1

#------------------------------------------------------------------------------
