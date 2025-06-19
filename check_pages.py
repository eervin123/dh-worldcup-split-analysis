import fitz
import re

doc = fitz.open("data/vdso_2025_dhi_me_results_tt.pdf")
print(f"Total pages: {len(doc)}")

for i in range(len(doc)):
    text = doc[i].get_text("text")
    lines = text.split("\n")
    riders = [line for line in lines if re.match(r"^\d+\s+[A-Z]", line)]
    print(f"Page {i+1}: {len(riders)} riders")

    # Show first few riders on each page
    for rider in riders[:3]:
        print(f"  {rider}")
    if len(riders) > 3:
        print(f"  ... and {len(riders)-3} more")
    print()

doc.close()
