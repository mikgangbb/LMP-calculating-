import geopandas as gpd

# 파일 경로
shp_file = "C:\\Users\\user\\Downloads\\ctprvn_20230729\\ctprvn.shp"

# SHP 파일 읽기
gdf = gpd.read_file(shp_file)

# GeoJSON으로 저장
geojson_file = "C:\\Users\\user\\Desktop\\비교과\\인사캠\\앙_files\\지리정보경계.geojson"
gdf.to_file(geojson_file, driver="GeoJSON")
print(f"GeoJSON 파일 저장 완료: {geojson_file}")
