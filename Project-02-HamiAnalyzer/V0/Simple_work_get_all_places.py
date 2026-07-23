import pandas as pd
data = pd.read_csv(r"/mnt/Data1/Python_Projects/Advanced-Python/Project-01-HamiWorks/V1/1_20903999340.csv")
data.columns = [str(i) for i in range(len(data.columns))]
# print(data)
new_data = pd.DataFrame(columns=["educational_level", "field", "city", "year", "count"])
for i, v in data.iterrows():
    splited = v["0"].split("_") if "_" in v["0"] else v["0"].split("-")
    try:
        if len(splited) == 4:
            educational_level, field, city, year = splited
        elif len(splited) == 5:
            educational_level, field, city, year = splited[0], splited[1] + "_" + splited[2], splited[3], splited[4]
        new_data.loc[len(new_data)] = {"educational_level": educational_level, "field": field, "city": city, "year": year, "count": v["2"]}
    except ValueError:
        print(f"Error processing row {i}: {v['0']} length is {len(v['0'].split('_')) if '_' in v['0'] else len(v['0'].split('-'))}")
new_data.to_csv(r"/mnt/Data1/Python_Projects/Advanced-Python/Project-01-HamiWorks/V1/output.csv", index=False, encoding="utf-8-sig")

data = pd.read_csv(r"/mnt/Data1/Python_Projects/Advanced-Python/Project-01-HamiWorks/V1/output.csv")
print(sum(data["count"]))

def map_educational_level(level):
    if "دکتری عمومی" in level:
        return "دکتری عمومی"
    elif "دکتری تخصصی" in level:
        return "دکتری تخصصی"
    elif "کارشناسی ارشد" in level:
        return "کارشناسی ارشد"
    elif "کارشناسی ناپیوسته" in level:
        return "کارشناسی ناپیوسته"
    elif "کارشناسی پیوسته" in level:
        return "کارشناسی پیوسته"
    elif "کاردانی" in level:
        return "کاردانی"
    else:
        print()
        print(level)
        print()

data["educational_level_group"] = data["educational_level"].apply(map_educational_level)
result = data.groupby("educational_level_group", dropna=True)["count"].sum().reset_index()
result = result[result["educational_level_group"].notna()]
result.to_csv(r"/mnt/Data1/Python_Projects/Advanced-Python/Project-01-HamiWorks/V1/educational_level_summary.csv", index=False, encoding="utf-8-sig")
# print(result)