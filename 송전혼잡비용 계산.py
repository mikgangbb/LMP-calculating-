import pandas as pd
from pulp import LpProblem, LpMinimize, LpVariable, lpSum

# 데이터 로드
dispatch_data = pd.read_csv("C:\Users\user\Desktop\비교과\인사캠\급전순위조회_권역추가.csv")  # 발전기: 연료비, 용량, 권역
demand_data = pd.read_csv("C:\Users\user\Desktop\비교과\인사캠\전력수요.csv")      # 권역별 전력 수요

# MILP 문제 정의
model = LpProblem(name="LMP_Calculation", sense=LpMinimize)

# 1. 결정 변수 정의
# 발전기 출력 (연속 변수)와 가동 상태 (이진 변수)
output_vars = {
    row['GeneratorName']: LpVariable(f"Output_{row['GeneratorName']}", lowBound=0, upBound=row['MaxCapacity'])
    for _, row in dispatch_data.iterrows()
}
status_vars = {
    row['GeneratorName']: LpVariable(f"Status_{row['GeneratorName']}", cat='Binary')
    for _, row in dispatch_data.iterrows()
}

# 2. 목표 함수 정의 (총 연료비 최소화)
model += lpSum(output_vars[gen] * dispatch_data.loc[dispatch_data['GeneratorName'] == gen, 'FuelCost'].values[0]
               for gen in output_vars)

# 3. 제약 조건 정의
# (1) 권역별 수요 충족
for region in demand_data['Region'].unique():
    demand = demand_data.loc[demand_data['Region'] == region, 'Demand'].values[0]
    region_generators = dispatch_data.loc[dispatch_data['Region'] == region, 'GeneratorName']
    model += lpSum(output_vars[gen] for gen in region_generators) == demand, f"Demand_{region}"

# (2) 발전기 상태와 출력 연계
for gen in output_vars:
    max_capacity = dispatch_data.loc[dispatch_data['GeneratorName'] == gen, 'MaxCapacity'].values[0]
    model += output_vars[gen] <= status_vars[gen] * max_capacity, f"StatusLink_{gen}"

# 4. 문제 풀기
model.solve()

# 5. 결과 추출
results = []
for gen in output_vars:
    output = output_vars[gen].value()
    status = status_vars[gen].value()
    fuel_cost = dispatch_data.loc[dispatch_data['GeneratorName'] == gen, 'FuelCost'].values[0]
    region = dispatch_data.loc[dispatch_data['GeneratorName'] == gen, 'Region'].values[0]
    results.append({
        'GeneratorName': gen,
        'Region': region,
        'Output': output,
        'Status': status,
        'FuelCost': fuel_cost,
        'Cost': output * fuel_cost if output else 0
    })

# 결과 데이터프레임 생성
results_df = pd.DataFrame(results)

# 권역별 LMP 계산
# LMP는 수요를 충족하는 한계 발전기의 연료비
region_lmp = results_df.groupby('Region').apply(lambda x: x[x['Output'] > 0]['FuelCost'].max()).reset_index()
region_lmp.columns = ['Region', 'LMP']

# 결과 출력
print("발전기별 결과:")
print(results_df)
print("\n권역별 LMP:")
print(region_lmp)
