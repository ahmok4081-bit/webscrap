import pandas as pd
from pathlib import Path

provinces = [
    "Banteay Meanchey", "Battambang", "Kampong Cham", "Kampong Chhnang", 
    "Kampong Speu", "Kampong Thom", "Kampot", "Kandal", "Kep", "Koh Kong", 
    "Kratié", "Mondulkiri", "Oddar Meanchey", "Pailin", "Phnom Penh", 
    "Preah Sihanouk", "Preah Vihear", "Prey Veng", "Pursat", "Ratanakiri", 
    "Siem Reap", "Stung Treng", "Svay Rieng", "Takéo", "Tboung Khmum"
]

populations = [
    898484, 1132017, 1062914, 604895, 924175, 807254, 682987, 1352198, 
    48772, 140962, 441078, 93657, 267703, 79445, 2352851, 234702, 
    249973, 1277867, 516072, 235852, 1099825, 176488, 613159, 1097243, 889970
]

# 1. Manual file write (Standard I/O)
with open('sakada.txt', 'w', encoding='utf-8') as file:
    file.write("Provinces,Population\n")
    for i in range(len(provinces)):
        file.write(f"{provinces[i]},{populations[i]}\n")

# 2. Using Pandas for structured Export
dict_provinces = {'Provinces': provinces, 'Populations': populations}
df_provinces = pd.DataFrame(dict_provinces)

# Set up the output path
# .parent.parent moves up two levels from where this script is located
output_path = Path(__file__).parent.parent / 'teste' / 'provinces_panha.csv'

# Create the directory if it doesn't exist; don't error if it does
output_path.parent.mkdir(parents=True, exist_ok=True)

# Save to CSV
df_provinces.to_csv(output_path, index=False)

print(f"Horray! Files saved to sakada.txt and {output_path}")