import pandas as pd
from pulp import LpProblem, LpMinimize, LpVariable, lpSum

# 파일 경로 설정
dispatch_data_path = r"C:\\Users\\user\\Desktop\\비교과\\인사캠\\급전순위조회_권역추가csv.csv"
demand_data_path = r"C:\\Users\\user\\Desktop\\비교과\\인사캠\\전력수요.csv"

# 데이터 로드
dispatch_data = pd.read_csv(dispatch_data_path, encoding='utf-8-sig')
demand_data = pd.read_csv(demand_data_path, encoding='euc-kr')

# 열 이름 정리
dispatch_data.columns = dispatch_data.columns.str.strip()
demand_data.columns = demand_data.columns.str.strip()

# 경제 급전 MILP 문제 정의
model = LpProblem(name="Economic_Dispatch", sense=LpMinimize)

# 결정 변수 정의
output_vars = {row['발전기명']: LpVariable(f"Output_{row['발전기명']}", lowBound=0, upBound=row['최대용량(95%)']) 
               for _, row in dispatch_data.iterrows()}
status_vars = {row['발전기명']: LpVariable(f"Status_{row['발전기명']}", cat='Binary') 
               for _, row in dispatch_data.iterrows()}

# 목적 함수 정의 (총 연료비 최소화)
model += lpSum(output_vars[gen] * dispatch_data.loc[dispatch_data['발전기명'] == gen, '연료비(원/kWh)'].values[0] 
               for gen in output_vars)

# 제약 조건 정의
# 1. 권역별 수요 충족
for region in demand_data['권역'].unique():
    region_generators = dispatch_data[dispatch_data['권역'] == region]['발전기명']
    demand = demand_data.loc[demand_data['권역'] == region, '전력수요(MWh)'].values[0]
    model += lpSum(output_vars[gen] for gen in region_generators) >= demand, f"Demand_{region}"

# 2. 발전기 출력 상태와 용량 연계
for gen in output_vars:
    max_capacity = dispatch_data.loc[dispatch_data['발전기명'] == gen, '최대용량(95%)'].values[0]
    model += output_vars[gen] <= status_vars[gen] * max_capacity, f"StatusLink_{gen}"

# 최적화 문제 해결
model.solve()

# 결과 추출
results = []
for gen in output_vars:
    output = output_vars[gen].value()
    status = status_vars[gen].value()
    fuel_cost = dispatch_data.loc[dispatch_data['발전기명'] == gen, '연료비(원/kWh)'].values[0]
    region = dispatch_data.loc[dispatch_data['발전기명'] == gen, '권역'].values[0]
    results.append({
        '발전기명': gen,
        '권역': region,
        '출력량(MWh)': output,
        '상태': status,
        '연료비(원/kWh)': fuel_cost,
        '총 비용(원)': output * fuel_cost if output else 0
    })

# 결과 데이터프레임 생성
results_df = pd.DataFrame(results)

# LMP 계산: 권역별 한계 발전기의 연료비
lmp_data = results_df.groupby('권역').apply(lambda x: x[x['출력량(MWh)'] > 0]['연료비(원/kWh)'].max()).reset_index()
lmp_data.columns = ['권역', 'LMP']

# 출력
print("발전기별 결과:")
print(results_df)
print("\\n권역별 LMP 결과:")
print(lmp_data)

# 결과 저장
results_df.to_csv(r"C:\\Users\\user\\Desktop\\LMP_MILP_결과.csv", index=False, encoding='utf-8')
lmp_data.to_csv(r"C:\\Users\\user\\Desktop\\LMP_권역별_결과.csv", index=False, encoding='utf-8')
