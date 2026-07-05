import subprocess, sys, os
os.chdir(r"c:\Users\jacob\OneDrive\Desktop\WATT-IF")
result = subprocess.run(
    [sys.executable, "-m", "pytest",
     "tests/model/test_sarimax_model.py",
     "-v", "--tb=short", "-p", "no:warnings"],
    capture_output=True, text=True, cwd=r"c:\Users\jacob\OneDrive\Desktop\WATT-IF"
)
output = result.stdout + result.stderr
with open("test_output.txt", "w") as f:
    f.write(output)
print(output[-5000:])  # print last 5000 chars
