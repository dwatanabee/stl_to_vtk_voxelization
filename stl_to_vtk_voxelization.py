# python3.X is only suppoorted．"pip3 install vtk"，"pip3 install pyevtk"
import vtk
import time
import numpy as np
import vtk.util.numpy_support as vnp

######## input data ########
# inport stl
filename_in = "jetEngineDesignDomainFine.stl"
# export vtk
filename_out = "out.vtk"
# mesh resolution
mesh_size = 200
# tolerance(about 10^-7~10^-3，smaller value is high accuracy.)
tol = 1e-7
# kind of voxel（"cubic" or "rect"）
cubicORrect = "cubic"
##################################

# main routine start
start = time.time()

# read stl
reader = vtk.vtkSTLReader()
reader.SetFileName(filename_in)
reader.Update()

closed_poly = reader.GetOutput()

# make mesh grid
# x_min:0 x_max:1, y_min:2,y_max:3,z_min:4,z_max:5
bounds = closed_poly.GetBounds()
max_size = max([bounds[1] - bounds[0], bounds[3] -
                bounds[2], bounds[5] - bounds[4]])
cell_dims = [mesh_size, mesh_size, mesh_size]  # x, y, z

if cubicORrect == "cubic":
    mesh_pitch = [max_size/cell_dims[0],
                  max_size/cell_dims[1],
                  max_size/cell_dims[2]]
else:
    mesh_pitch = [(bounds[1] - bounds[0])/cell_dims[0],
                  (bounds[3] - bounds[2])/cell_dims[1],
                  (bounds[5] - bounds[4])/cell_dims[2]]

mins = [bounds[0], bounds[2], bounds[4]]


px, py, pz = mesh_pitch
mx, my, mz = (cell_dims+np.array([1, 1, 1])) * mesh_pitch  # max
points = vtk.vtkPoints()
coords = np.stack(np.mgrid[:mx:px, :my:py, :mz:pz], -1).reshape(-1, 3) + mins
points.SetData(vnp.numpy_to_vtk(coords))

structured_base_mesh = vtk.vtkStructuredGrid()
structured_base_mesh.SetExtent(
    0, cell_dims[0], 0, cell_dims[1], 0, cell_dims[2])
structured_base_mesh.SetPoints(points)

# structured to unstructured
append = vtk.vtkAppendFilter()
append.AddInputData(structured_base_mesh)
append.Update()
base_mesh = append.GetOutput()

# get center of Voxel
cell_centers = vtk.vtkCellCenters()
cell_centers.SetInputData(base_mesh)
cell_centers.Update()

poly_points = cell_centers.GetOutput()

# judge inside or outside with vtkSelectEnclosedPoints
select_enclosed = vtk.vtkSelectEnclosedPoints()
select_enclosed.SetInputData(poly_points)
select_enclosed.SetSurfaceData(closed_poly)
select_enclosed.SetTolerance(tol)
select_enclosed.Update()

# Referring to the array "SelectedPoints" and giving it to the CellData of baseMesh
isInsideOrOutside = select_enclosed.GetOutput(
).GetPointData().GetArray("SelectedPoints")
structured_base_mesh.GetCellData().AddArray(isInsideOrOutside)

# Extract information from an array called "SelectedPoints" hanging from the CellData of the shape.
threshold = vtk.vtkThreshold()
threshold.SetInputArrayToProcess(
    0, 0, 0, vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS, "SelectedPoints")
threshold.SetInputData(structured_base_mesh)
threshold.ThresholdBetween(1, 1)
threshold.Update()

# export vtk(legacy, ascii)
writer = vtk.vtkDataSetWriter()
writer.SetFileName(filename_out)
writer.SetInputData(threshold.GetOutput())
writer.Update()

elapsed_time = time.time() - start
print("computation time:{0}".format(elapsed_time) + "[sec]")
