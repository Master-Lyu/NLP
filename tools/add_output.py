import json

def add_output_field(file_path):
    try:
        # 读取原始 JSON 文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 遍历处理数据
        def process_item(item):
            if isinstance(item, dict):
                # 创建新字典以保持字段顺序
                new_item = {}
                inserted_output = False
                
                # 遍历原始字段
                for key, value in item.items():
                    new_item[key] = value
                    # 在 input 后插入 output
                    if key == "input" and not inserted_output:
                        new_item["output"] = ""
                        inserted_output = True
                
                # 如果没有 input，就在末尾添加 output
                if not inserted_output:
                    new_item["output"] = ""
                return new_item
            return item
        
        # 处理不同类型的数据结构
        if isinstance(data, list):
            processed_data = [process_item(item) for item in data]
        elif isinstance(data, dict):
            processed_data = process_item(data)
        else:
            raise ValueError("Unsupported JSON structure")
        
        # 写入修改后的文件（保留原始格式）
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)
            f.write('\n')  # 添加结尾换行符保持文件整洁
        
        return "成功在所有 'input' 字段后添加了 'output' 字段"
    
    except Exception as e:
        return f"处理文件时出错: {str(e)}"

# 调用函数处理指定文件
result = add_output_field("test1.json")
print(result)