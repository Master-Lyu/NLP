import json

input_path = 'generated_predictions_3.json'
output_path = 'predicts_only_3.txt'

predicts = []
with open(input_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue  # 跳过空行
        item = json.loads(line)
        if "predict" in item:
            # 替换predict中的所有换行符为空格，避免写入txt时多行
            pred = item["predict"].replace('\n', ' ').strip()
            predicts.append(pred)

# 写入到 txt 文件，每行一个 predict 的内容
with open(output_path, 'w', encoding='utf-8') as out_f:
    for i, pred in enumerate(predicts):
        out_f.write(pred)
        if i != len(predicts) - 1:
            out_f.write('\n')

# 比较两文件行数
with open('generated_predictions_3.json', 'r', encoding='utf-8') as f1, \
     open('predicts_only_3.txt', 'r', encoding='utf-8') as f2:
    json_lines = sum(1 for line in f1 if line.strip())
    txt_lines = sum(1 for line in f2 if line.strip())
print(f'json: {json_lines}, txt: {txt_lines}')