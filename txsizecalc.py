import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import math

def get_log_group(number):
    if number <= 0:
        return "≤0"
    return int(math.log10(number))

# Read numbers from the file
with open('dump.txt', 'r') as file:
    numbers = [float(line.strip()) for line in file]

# Group numbers and count occurrences
groups = defaultdict(lambda: {"count": 0, "sum": 0})
for num in numbers:
    group = get_log_group(num)
    groups[group]["count"] += 1
    groups[group]["sum"] += num

# Calculate totals
total_count = sum(group["count"] for group in groups.values())
total_sum = sum(group["sum"] for group in groups.values())

# Prepare data for plotting
sorted_groups = sorted(groups.items(), key=lambda x: x[0] if x[0] != "≤0" else -float('inf'))
labels = []
count_percentages = []
sum_percentages = []

for group, data in sorted_groups:
    if group == "≤0":
        label = "≤0"
    else:
        lower = 10 ** group
        upper = 10 ** (group + 1)
        label = f"{lower}-{upper}"
    
    count_percentage = (data["count"] / total_count) * 100
    sum_percentage = (data["sum"] / total_sum) * 100
    
    labels.append(label)
    count_percentages.append(count_percentage)
    sum_percentages.append(sum_percentage)

# Create the grouped bar chart
x = np.arange(len(labels))
width = 0.35

fig, ax = plt.subplots(figsize=(15, 8))
rects1 = ax.bar(x - width/2, count_percentages, width, label='% of Total Count')
rects2 = ax.bar(x + width/2, sum_percentages, width, label='% of Total Sum')

ax.set_ylabel('Percentage')
ax.set_title('Distribution of Numbers by Count and Sum (Logarithmic Scale)')
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha='right')
ax.legend()

# Add value labels on top of each bar
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.2f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', rotation=90)

autolabel(rects1)
autolabel(rects2)

fig.tight_layout()
plt.show()