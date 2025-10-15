import math
from typing import List

class PatientVoxel:
    def __init__(self, x, y, structure_code):
        self.x =  float(x)
        self.y = -float(y) # Excel file has +y down, internal coords are +y up
        self.structure_code = structure_code
        self.transformed_x = self.x
        self.transformed_y = self.y

    def __repr__(self):
        return f"PatientVoxel(x={self.x}, y={self.y}, structure_code={self.structure_code})"
    
class PatientData:
    def __init__(self):
        self.voxels:List[PatientVoxel] = []
        self.min_x = None
        self.max_x = None
        self.min_y = None
        self.max_y = None
        self.center_x = None
        self.center_y = None
        self.stride = None # Number of elements per row, set when loading data

    # Add a voxel and update min/max coordinates to keep track of center to rotate around
    def add_voxel(self, voxel: PatientVoxel):
        self.voxels.append(voxel)
        if self.min_x is None or voxel.x < self.min_x:
            self.min_x = voxel.x
        if self.max_x is None or voxel.x > self.max_x:
            self.max_x = voxel.x
        if self.min_y is None or voxel.y < self.min_y:
            self.min_y = voxel.y
        if self.max_y is None or voxel.y > self.max_y:
            self.max_y = voxel.y

        self.center_x = (self.min_x + self.max_x) / 2.0
        self.center_y = (self.min_y + self.max_y) / 2.0

    # Initialize Patient Data from a CSV file
    def load_from_csv(self, file_path: str) -> 'PatientData':
        with open(file_path, "r") as f:
            lines = f.readlines()

            # 0th line are x coordinates
            x_coords = lines[0].strip().split(",")[1:]  # the 0th element is the top-left corner and no elements have it as a coordinate
             
            # Remaining lines are y coordinates in the 0th column and then the structure codes
            for l in lines[1:]:
                # Extract y coordinate at the start of the line
                row_elements = l.strip().split(",")
                y_coord = row_elements[0]

                # Set stride if not already set, otherwise ensure it's consistent
                if self.stride is None:
                    self.stride = len(row_elements) - 1
                elif self.stride != len(row_elements) - 1:
                    raise ValueError("Inconsistent number of x coordinates in patient data file")

                # Add each voxel in this row
                patient_voxel_data = row_elements[1:]
                for index in range(len(patient_voxel_data)):
                    structure_code = patient_voxel_data[index]
                    new_voxel = PatientVoxel(x_coords[index], y_coord, structure_code)

                    self.add_voxel(new_voxel)

    # Transform the patient data by rotating around the center by a given angle in degrees
    def rotate(self, angle_degrees: float):
        angle_radians = math.radians(angle_degrees)
        cos_angle = math.cos(angle_radians)
        sin_angle = math.sin(angle_radians)

        for voxel in self.voxels:
            # Translate voxel to origin
            translated_x = voxel.x - self.center_x
            translated_y = voxel.y - self.center_y

            # Rotate around origin
            rotated_x = translated_x * cos_angle - translated_y * sin_angle
            rotated_y = translated_x * sin_angle + translated_y * cos_angle

            # Translate back
            voxel.transformed_x = rotated_x + self.center_x
            voxel.transformed_y = rotated_y + self.center_y

    # Look for the most-positive (in our coordinate system) with a structure
    # code that isn't 'Air' to be able to apply depth dose data.
    def find_surface(self) -> float:
        surface_y = None
        for voxel in self.voxels:
            if voxel.structure_code != "A":
                if surface_y is None or voxel.transformed_y > surface_y:
                    surface_y = voxel.transformed_y

        return surface_y
    
class BeamData:
    def __init__(self):
        self.off_axis_coordinates:List[float] = []
        self.depths:List[float] = []

        self.doses:List[float] = []

    # Load depth dose data from a CSV file
    def load_from_csv(self, file_path: str) -> 'DepthDoseData':
        with open(file_path, "r") as f:
            lines = f.readlines()

            # lines[0] and lines[1] are text headers
            # lines[2] = depths, except the 0th entry is blank;  Convert from string to floats
            self.depths = [float(x) for x in lines[2].strip().split(",")[1:]]

            # Remaining lines are dose values at each off-axis coordinate
            # where the 0th entry is the off-axis coordinate, then percent dose values
            for l in lines[3:]:
                row_elements = l.strip().split(",")
                off_axis_coord = float(row_elements[0])
                self.off_axis_coordinates.append(off_axis_coord)

                dose_values = [float(x) for x in row_elements[1:]]
                if len(dose_values) != len(self.depths):
                    raise ValueError("Dose values count does not match depths count")
                
                self.doses.extend(dose_values)

    # Get dose at specific 0-based list index
    def get_dose_at_index(self, off_axis_index: int, depth_index: int) -> float:
        if off_axis_index < 0 or off_axis_index >= len(self.off_axis_coordinates):
            raise IndexError("Off-axis index out of range")
        if depth_index < 0 or depth_index >= len(self.depths):
            raise IndexError("Depth index out of range")
        
        dose_index = off_axis_index * len(self.depths) + depth_index
        return self.doses[dose_index]

    # Get dose at a specific depth using linear interpolation
    def get_dose_at_depth(self, off_axis_value:float, depth: float) -> float:
        # Get the index of the off-axis coordinate that most closely matches.
        # These are sorted in ascending order based on the data file's format.
        off_axis_index = len(self.off_axis_coordinates) - 1
        for i in range(len(self.off_axis_coordinates)):
            if self.off_axis_coordinates[i] > off_axis_value:
                off_axis_index = i-1
                break
        
        # Get the index of the depth that most closely matches, analogously
        depth_index = len(self.depths) - 1
        for i in range(len(self.depths)):
            if self.depths[i] > depth:
                depth_index = i-1
                break

        # Get 4 values to interpolate between
        d1 = self.get_dose_at_index(off_axis_index,   depth_index)
        d2 = self.get_dose_at_index(off_axis_index+1, depth_index)

        # Interpolate in the off-axis direction first
        delta_coord  = self.off_axis_coordinates[off_axis_index+1] - self.off_axis_coordinates[off_axis_index]
        delta_target = off_axis_value - self.off_axis_coordinates[off_axis_index]
        d1_2 = d1 + (d2 - d1) * (delta_target / delta_coord)

        # Interpolate similarly for the next depth
        d3 = self.get_dose_at_index(off_axis_index,   depth_index+1)
        d4 = self.get_dose_at_index(off_axis_index+1, depth_index+1)
        d3_4 = d3 + (d4 - d3) * (delta_target / delta_coord)

        # Now interpolate between d1_2 and d3_4 in the depth direction
        delta_depth  = self.depths[depth_index+1] - self.depths[depth_index]
        delta_target = depth - self.depths[depth_index]
        final_dose = d1_2 + (d3_4 - d1_2) * (delta_target / delta_depth)

        return final_dose

class TreatmentPlan:
    def __init__(self, patient:PatientData):
        self.patient = patient

        # Initialize dose distribution to zero
        self.dose_distribution:List[float] = [0.0] * len(patient.voxels)

    def treat_with_beam_at_angle(self, beam:BeamData, angle_degrees:float):
        # Rotate patient data to match beam angle
        self.patient.rotate(angle_degrees)

        # Find the surface y (most-positive) with a structure code that isn't 'Air'
        surface_y = self.patient.find_surface()
        if surface_y is None:
            raise ValueError("No surface found in patient data")

        # For each voxel, determine its depth and get dose from beam data
        for i, voxel in enumerate(self.patient.voxels):
            depth = surface_y - voxel.transformed_y  # Depth is positive going into the patient
            if depth < 0:
                raise ValueError("Voxel is above the surface, which should not happen, surface must be incorrect")

            dose = beam.get_dose_at_depth(voxel.transformed_x, depth)
            self.dose_distribution[i] += dose

    def output_dose_distribution(self):
        for i, voxel in enumerate(self.patient.voxels):
            print(f"Voxel at ({voxel.transformed_x:.2f}, {voxel.transformed_y:.2f}) with structure '{voxel.structure_code}' receives dose: {self.dose_distribution[i]:.2f}", end="")
            if i % self.patient.stride == 0 and i != 0:
                print() # New line at end of each row

#### MAIN ENTRY POINT ####
patient_data = PatientData()
patient_data.load_from_csv("ProstateDataFile-patient.csv")

beam_data = BeamData()
beam_data.load_from_csv("ProstateDataFile-5x5-open.csv")

treatment_plan = TreatmentPlan(patient_data)
treatment_plan.treat_with_beam_at_angle(beam_data, 0.0) # AP direction
treatment_plan.output_dose_distribution()


# for voxel in patient_data.voxels:
#     if voxel.structure_code == "P":
#         print(f"Prostate voxel found after rotation at ({voxel.transformed_x:.2f}, {-voxel.transformed_y:.2f})")