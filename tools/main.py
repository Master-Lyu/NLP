import json
import re
from ollama import Client
from tqdm import tqdm

# 初始化本地 Ollama 客户端
local_client = Client(host="http://localhost:11434")

# 读取测试集
def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

# 构造 prompt
def build_prompt(text):
    prompt = f"""你是一个内容审查专家，请你分析我的句子并且从中提取出一个或者多个四元组。请从下面的文本抽取一个或多个四元组，每一个四元组输出格式为评论对象|对象观点|是否仇恨|仇恨群体。评论对象可以为'NULL',对象观点尽量简洁,仇恨群体只包括(LGBTQ、Region、Sexism、Racism、others、non-hate)，同一四元组可能涉及多个仇恨群体，是否仇恨标签为(hate、non-hate),多个四元组之间用[SEP]分隔,最后一个四元组后面加[END]。提取出句子中包含的所有四元组:
输入：{text}
输出："""
    return prompt

# 过滤掉 <think> 标签及其内容
def filter_think_tags(response):
    # 使用正则表达式移除 <think> 和 </think> 标签及其间的内容
    clean_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    # 移除可能残留的空行
    clean_response = re.sub(r'\n\s*\n', '\n', clean_response).strip()
    return clean_response

# 调用大模型
def extract_quadruples(text):
    prompt = build_prompt(text)
    response = local_client.generate(
        model="deepseek-r1:7b",
        prompt=prompt,
        options={"temperature": 0.2, "max_tokens": 256}
    )
    # 过滤掉思考过程
    clean_response = filter_think_tags(response['response'])
    return clean_response.strip()

# 主处理流程
def process_and_save(input_files, output_file):
    # 清空或创建输出文件
    open(output_file, 'w').close()
    
    # 初始化结果缓冲区
    results_buffer = []
    
    for file in input_files:
        data = load_json(file)
        for idx, item in enumerate(tqdm(data, desc=f"Processing {file}")):
            # 读取 content 字段
            if isinstance(item, dict):
                text = item.get('content', '')  # 防止没有'content'字段
            else:
                text = item
            result = extract_quadruples(text)
            results_buffer.append(result)
            
            # 每10条保存一次
            if (idx + 1) % 10 == 0:
                with open(output_file, 'a', encoding='utf-8') as f:
                    for res in results_buffer:
                        f.write(res + '\n')
                results_buffer = []  # 清空缓冲区
    
    # 保存剩余结果
    if results_buffer:
        with open(output_file, 'a', encoding='utf-8') as f:
            for res in results_buffer:
                f.write(res + '\n')

if __name__ == "__main__":
    # 你可以根据实际情况修改文件名
    input_files = ['test1.json']
    output_file = 'output.txt'
    process_and_save(input_files, output_file)
    print(f"已完成，结果保存在 {output_file}")