import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import numpy as np
import altair as alt

# CSV 파일 경로 설정
results_file = r"비교과\\인사캠\\발전기별 결과.csv"
lmp_file = r"비교과\\인사캠\\LMP_권역별_결과.csv"
geojson_file = r"비교과\\인사캠\\TL_SCCO_CTPRVN.json"


# 데이터 로드
@st.cache
def load_data():
    results_df = pd.read_csv(results_file, encoding='utf-8')
    lmp_df = pd.read_csv(lmp_file, encoding='utf-8')
    
    with open(geojson_file, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)
    
    return results_df, lmp_df, geojson_data

results_df, lmp_df, geojson_data = load_data()

# LMP 권역별 시각화
st.header("권역별 LMP")
st.dataframe(lmp_df)

# 데이터 시각화 - 표 및 그래프
st.title("LMP 및 발전기별 출력량 시각화")

# 발전기별 출력량 및 비용 표시
st.header("발전기별 출력량 및 비용")
st.dataframe(results_df)

# 발전기별 출력량 차트
st.subheader("발전기별 출력량 (MWh)")
chart = alt.Chart(results_df).mark_bar().encode(
    x='발전기명',
    y='출력량(MWh)',
    color='권역',
    tooltip=['발전기명', '권역', '출력량(MWh)', '총 비용(원)']
).interactive()
st.altair_chart(chart, use_container_width=True)

# 사이드바: 신재생 에너지 전환 비율 조정
st.sidebar.title("전남 신재생 에너지 전환 비율")
renewable_rate = st.sidebar.slider("전환 비율 (%)", min_value=0, max_value=100, value=50)

# 신재생 전환 비율을 0~1로 변환
renewable_rate_normalized = renewable_rate / 100

# 비선형 감소 파라미터 설정 (α 값 조정 가능)
alpha = 4

# 전남 지역의 LMP 값 조정 (비선형 감소 적용)
original_lmp = lmp_df.loc[lmp_df['권역'] == "호남", 'LMP'].values[0]
adjusted_lmp = original_lmp * np.exp(-alpha * renewable_rate_normalized)
lmp_df.loc[lmp_df['권역'] == "호남", 'LMP'] = adjusted_lmp

# 신재생 에너지 적용 후 전남 LMP 값 출력
st.sidebar.write(f"신재생 에너지 적용 후 전남 LMP: {adjusted_lmp:.2f} 원/kWh")

# 권역 이름 매핑 (GeoJSON과 LMP 데이터를 연결)
name_mapping = {
    "서울특별시": "수도",
    "인천광역시": "수도",
    "경기도": "수도",
    "강원도": "강원",
    "충청북도": "충청",
    "충청남도": "충청",
    "대전광역시": "충청",
    "세종특별자치시": "충청",
    "전라북도": "호남",
    "전라남도": "호남",
    "광주광역시": "호남",
    "경상북도": "경북",
    "경상남도": "경남",
    "울산광역시": "경남",
    "부산광역시": "경남",
    "제주특별자치도": "제주"
}

# GeoJSON 데이터에 권역 정보 추가
for feature in geojson_data["features"]:
    region_name = feature["properties"]["CTP_KOR_NM"]
    feature["properties"]["권역"] = name_mapping.get(region_name, region_name)

# LMP 값을 GeoJSON 데이터에 추가
for feature in geojson_data["features"]:
    region = feature["properties"]["권역"]
    lmp_value = lmp_df.loc[lmp_df['권역'] == region, 'LMP'].values
    feature["properties"]["LMP"] = float(lmp_value[0]) if len(lmp_value) > 0 else None

# Folium 지도 생성
m = folium.Map(location=[36.5, 127.5], zoom_start=7)

# LMP 값의 범위를 기반으로 Choropleth 추가
folium.Choropleth(
    geo_data=geojson_data,
    name="choropleth",
    data=lmp_df,
    columns=["권역", "LMP"],
    key_on="feature.properties.권역",
    fill_color="YlGnBu",  # 색상 팔레트 이름
    fill_opacity=0.7,
    line_opacity=0,
    legend_name="LMP 값 (원/kWh)"
).add_to(m)

# 팝업 추가
for feature in geojson_data["features"]:
    region_name = feature["properties"]["권역"]
    lmp_value = feature["properties"]["LMP"]
    if lmp_value is not None:
        folium.GeoJson(
            feature,
            tooltip=f"{region_name}<br>LMP: {lmp_value:.2f} 원/kWh"
        ).add_to(m)

# Streamlit에서 Folium 지도 렌더링
st_folium(m, width=800, height=600)
