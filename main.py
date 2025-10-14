
class PatientVoxel:
    def __init__(self, x, y, structure_code):
        self.x = float(x)
        self.y = float(y)
        self.structure_code = structure_code

    def __repr__(self):
        return f"PatientVoxel(x={self.x}, y={self.y}, structure_code={self.structure_code})"


#### MAIN ENTRY POINT ####
patient_data = []

with open("ProstateDataFile-patient.csv", "r") as f:
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
            patient_data.append(PatientVoxel(x_coords[index], y_coord, structure_code))


# Find the center of the patient so that rotations are symmetric
# Get min and max x and y coordinates
min_x = min(voxel.x for voxel in patient_data)
max_x = max(voxel.x for voxel in patient_data)
min_y = min(voxel.y for voxel in patient_data)
max_y = max(voxel.y for voxel in patient_data)

for voxel in patient_data:
    if voxel.structure_code == "P":
        print(f"Prostate voxel found at ({voxel.x * 1.0}, {voxel.y})")

center_x = (min_x + max_x) / 2.0
center_y = (min_y + max_y) / 2.0

print(f"Center of patient is at ({center_x}, {center_y})")