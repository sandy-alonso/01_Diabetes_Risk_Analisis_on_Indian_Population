import kagglehub
import shutil

path = kagglehub.dataset_download("yashlakra37/indian-diabetes-risk-csv")
shutil.copytree(path, "../data/raw", dirs_exist_ok=True)
print("Data downloaded and copied to ../data/raw")