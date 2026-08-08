import pandas as pd

# Path to your GeoJSON file
geojson_file = "world.geojson"
csv_file = "world.csv"

# Load and flatten the GeoJSON
df = pd.json_normalize(pd.read_json(geojson_file)["features"])

# Keep only the properties columns and remove the "properties." prefix
properties_df = df.filter(like="properties.").rename(
    columns=lambda x: x.replace("properties.", "")
)

# Save to CSV
properties_df.to_csv(csv_file, index=False, encoding="utf-8")

print(f"✅ CSV file saved as: {csv_file}")
print("\nPreview of data:")
print(properties_df.head())
