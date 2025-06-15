import json

# 定义新的instruction文本
new_instruction = (
    "你是一个内容审查专家，请你分析我的句子并且从中提取出一个或者多个四元组。"
    "请从下面的文本抽取一个或多个四元组，每一个四元组输出格式为评论对象|对象观点|是否仇恨|仇恨群体。"
    "评论对象可以为'NULL',对象观点尽量简洁,仇恨群体只包括(LGBTQ、Region、Sexism、Racism、others、non-hate)，"
    "同一四元组可能涉及多个仇恨群体，是否仇恨标签为(hate、non-hate),多个四元组之间用[SEP]分隔,最后一个四元组后面加[END]。"
    "提取出句子中包含的所有四元组:"
)

# 读取原始JSON文件
with open('train.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 更新每个条目的instruction字段
for item in data:
    item['instruction'] = new_instruction

# 保存修改后的JSON文件
with open('train.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("文件已更新并保存为 train.json")