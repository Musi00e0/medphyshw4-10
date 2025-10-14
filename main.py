import math

class PatientVoxel:
    def __init__(self, x, y, structure_code):
        self.x = float(x)
        self.y = float(y)
        self.structure_code = structure_code

    def __repr__(self):
        return f"PatientVoxel(x={self.x}, y={self.y}, structure_code={self.structure_code})"
    
class PatientData:
    def __init__(self):
        self.voxels = []
        self.min_x = None
        self.max_x = None
        self.min_y = None
        self.max_y = None
        self.center_x = None
        self.center_y = None

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
                row_elements = l.strip().split(",")
                y_coord = row_elements[0]

                patient_voxel_data = row_elements[1:]
                for index in range(len(patient_voxel_data)):
                    structure_code = patient_voxel_data[index]
                    new_voxel = PatientVoxel(x_coords[index], y_coord, structure_code)

                    self.add_voxel(new_voxel)

    # Transform the patient data by rotating around the center by a given angle in degrees
    def rotate(self, angle_degrees: float) -> 'PatientData':
        angle_radians = math.radians(angle_degrees)
        cos_angle = math.cos(angle_radians)
        sin_angle = math.sin(angle_radians)

        rotated_data = PatientData()

        for voxel in self.voxels:
            # Translate voxel to origin
            translated_x = voxel.x - self.center_x
            translated_y = voxel.y - self.center_y

            # Rotate around origin
            rotated_x = translated_x * cos_angle - translated_y * sin_angle
            rotated_y = translated_x * sin_angle + translated_y * cos_angle

            # Translate back
            final_x = rotated_x + self.center_x
            final_y = rotated_y + self.center_y

            rotated_voxel = PatientVoxel(final_x, final_y, voxel.structure_code)
            rotated_data.add_voxel(rotated_voxel)

        return rotated_data

#### MAIN ENTRY POINT ####
patient_data = PatientData()
patient_data.load_from_csv("ProstateDataFile-patient.csv")

for voxel in patient_data.voxels:
    if voxel.structure_code == "P":
        print(f"Prostate voxel found at ({voxel.x * 1.0}, {voxel.y})")

print(f"Center of patient is at ({patient_data.center_x}, {patient_data.center_y})")