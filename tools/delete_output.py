import json

def clear_output_values(input_file, output_file):
    """
    清除JSON文件中所有output字段的值
    
    参数:
    input_file: 输入JSON文件路径
    output_file: 输出JSON文件路径
    """
    # 1. 读取原始JSON文件
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 2. 递归处理嵌套结构
    def process_item(item):
        if isinstance(item, dict):
            for key in item:
                if key == "output":
                    item[key] = ""
                else:
                    # 递归处理嵌套结构
                    process_item(item[key])
        elif isinstance(item, list):
            for element in item:
                process_item(element)
    
    # 3. 处理整个数据结构
    process_item(data)
    
    # 4. 保存修改后的JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# 调用函数处理文件
input_file = "test1.json"
output_file = "test1.json"
clear_output_values(input_file, output_file)

print(f"处理完成！已创建新文件: {output_file}")