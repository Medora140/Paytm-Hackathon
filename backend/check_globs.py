import os
import glob

print("Matching Desktop/Paytm*:")
for p in glob.glob(r"C:\Users\Medora Gomes\Desktop\*Paytm*") + glob.glob(r"C:\Users\Medora Gomes\Desktop\*paytm*"):
    print(f"  {p}")

print("Matching Downloads/*Money*:")
for p in glob.glob(r"C:\Users\Medora Gomes\Downloads\*Money*") + glob.glob(r"C:\Users\Medora Gomes\Downloads\*money*"):
    print(f"  {p}")
