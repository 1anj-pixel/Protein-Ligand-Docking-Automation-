import os
import subprocess
import csv
import time

# Define paths
receptor_folder = "receptor"
ligand_folder = "ligand"
output_folder = "docking_results"
log_folder = "log_files"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

# CSV output file
output_csv = "docking_results.csv"

# Prepare CSV header
with open(output_csv, mode="wb") as csv_file:  # 'wb' for binary mode in Python 2
    writer = csv.writer(csv_file)
    writer.writerow(["Receptor", "Ligand", "Highest Binding Affinity"])

# Docking batch parameters
batch_size = 20
pause_duration = 30  # 30 seconds pause

# Loop through each receptor and ligand with batch processing
dock_count = 0  # Counter for docking operations
first_batch_skipped = False  # Flag to indicate if the first batch is skipped

for receptor_file in os.listdir(receptor_folder):
    if receptor_file.endswith(".pdbqt"):
        receptor_path = os.path.join(receptor_folder, receptor_file)
        
        for ligand_file in os.listdir(ligand_folder):
            if ligand_file.endswith(".pdbqt"):
                ligand_path = os.path.join(ligand_folder, ligand_file)
                
                # Increment docking count and check if we should skip the first batch
                dock_count += 1
                if dock_count <= batch_size and not first_batch_skipped:
                    # Skip the first batch of 20 dockings
                    if dock_count == batch_size:
                        first_batch_skipped = True
                    continue  # Skip this docking operation

                # Output file for docking results and log file for this pair
                output_file = os.path.join(output_folder, "{}_{}_out.pdbqt".format(receptor_file, ligand_file))
                log_file = os.path.join(log_folder, "{}_{}_log.txt".format(receptor_file, ligand_file))
                
                # Run docking command with Vina or Smina and save log
                with open(log_file, "w") as log:
                    subprocess.call([
                        "vina",  # replace with "smina" if using Smina
                        "--receptor", receptor_path,
                        "--ligand", ligand_path,
                        "--out", output_file,
                        "--center_x", "0", "--center_y", "0", "--center_z", "0",
                        "--size_x", "50", "--size_y", "50", "--size_z", "50"
                    ], stdout=log, stderr=subprocess.STDOUT)
                
                # Extract the highest binding affinity from line 27 of the log file
                affinity = None
                with open(log_file, "r") as log:
                    lines = log.readlines()
                    if len(lines) >= 27:
                        target_line = lines[26]  # Index 26 since it's zero-based
                        extracted_value = target_line[12:19].strip()  # Columns 13-19 (1-based indexing)
                        try:
                            affinity = float(extracted_value)
                        except ValueError:
                            affinity = "Invalid format"
                    else:
                        affinity = "Line 27 does not exist"
                
                # Remove file extensions from receptor and ligand filenames
                receptor_name = os.path.splitext(receptor_file)[0]
                ligand_name = os.path.splitext(ligand_file)[0]
                
                # If affinity is found, add to CSV
                with open(output_csv, mode="ab") as csv_file:  # 'ab' for appending in binary mode in Python 2
                    writer = csv.writer(csv_file)
                    writer.writerow([receptor_name, ligand_name, affinity])

                # Pause after each batch except the skipped first batch
		if (dock_count - batch_size) % batch_size == 0:
                    print "Batch of {} dockings completed. Pausing for {} seconds...".format(batch_size, pause_duration)
                    time.sleep(pause_duration)
                    print "Resuming docking..."

print "Docking completed. Results saved in {} and log files saved in {}".format(output_csv, log_folder)
