#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
细粒度中文仇恨言论四元组识别模型集成工具

本脚本实现了基于优先级规则的投票集成机制，用于合并两个预训练语言模型
(Qwen2.5-7B-instruct和Qwen3-8B-instruct)的四元组抽取结果。
集成算法基于以下原则：
1. 保留两模型共同预测的四元组（高置信度）
2. 对仅被单一模型预测的四元组：
   - 优先保留含仇恨标记(hate/yes)的四元组，提高敏感内容召回
   - 对非仇恨四元组，采用软投票机制(阈值0.6)控制保留比例
"""

import os
import random
import logging
import argparse
from typing import List, Tuple, Dict, Set
import time

# 配置日志输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 定义四元组类型别名，提高代码可读性
Quadruple = Tuple[str, str, str, str]


def parse_quadruples(line: str) -> List[Quadruple]:
    """
    解析模型输出行，提取所有四元组
    
    Args:
        line: 包含多个四元组的预测结果行，格式为"对象|论点|群体|标签 [SEP] ..."
    
    Returns:
        四元组列表，每个四元组为(target, argument, group, hateful)元组
    """
    results = []
    # 按[SEP]分割多个四元组
    segments = line.strip().split('[SEP]')
    
    for segment in segments:
        # 清理空白字符
        part = segment.strip()
        # 移除可能的[END]标记
        if part.endswith('[END]'):
            part = part[:-5].strip()
        if not part:  # 跳过空段
            continue
            
        # 按|分割四元组各字段
        fields = [x.strip() for x in part.split('|')]
        if len(fields) == 4:  # 确保是完整四元组
            results.append(tuple(fields))
        else:
            logger.warning(f"忽略非标准四元组格式: {part} (字段数: {len(fields)})")
    
    return results


def ensemble_predictions(
    quads1: List[Quadruple], 
    quads2: List[Quadruple], 
    hate_priority: bool = True,
    nonhate_threshold: float = 0.6,
    random_seed: int = 42
) -> List[Quadruple]:
    """
    基于规则优先级的集成策略，合并两个模型的四元组预测
    
    Args:
        quads1: 第一个模型(Qwen2.5)预测的四元组列表
        quads2: 第二个模型(Qwen3)预测的四元组列表
        hate_priority: 是否优先保留带hate标记的四元组
        nonhate_threshold: 非仇恨四元组的保留阈值(0.0-1.0)
        random_seed: 随机数种子，用于软投票决策
        
    Returns:
        集成后的四元组列表
    """
    # 为保证结果可复现，设置随机种子
    random.seed(random_seed)
    
    # 将四元组转换为集合以便操作
    set1 = set(quads1)
    set2 = set(quads2)
    
    # 分离交集与差集
    common_quads = set1.intersection(set2)  # 两模型共同预测的四元组
    unique_quads = set1.symmetric_difference(set2)  # 仅被单一模型预测的四元组
    
    # 初始化结果集，首先加入所有交集元素（高置信度）
    result_quads = list(common_quads)
    
    # 处理差集元素
    for quad in unique_quads:
        hateful_label = quad[3].lower()
        
        # 策略1: 优先保留hate/yes标记的四元组
        if hate_priority and (hateful_label == "hate" or hateful_label == "yes"):
            result_quads.append(quad)
        
        # 策略2: 非仇恨四元组使用软投票阈值决定是否保留
        elif random.random() < nonhate_threshold:
            result_quads.append(quad)
    
    return result_quads


def format_output(quadruples: List[Quadruple]) -> str:
    """
    将四元组列表格式化为提交所需字符串
    
    Args:
        quadruples: 四元组列表
        
    Returns:
        格式化后的字符串，四元组间用[SEP]分隔，以[END]结尾
    """
    if not quadruples:
        return "[END]"
        
    parts = [" | ".join(quad) for quad in quadruples]
    return " [SEP] ".join(parts) + " [END]"


def main():
    """主函数，处理命令行参数并执行集成流程"""
    parser = argparse.ArgumentParser(description="细粒度中文仇恨言论四元组识别模型集成工具")
    
    parser.add_argument("--file1", type=str, required=True, 
                        help="Qwen2.5-7B-instruct模型预测结果文件路径")
    parser.add_argument("--file2", type=str, required=True, 
                        help="Qwen3-8B-instruct模型预测结果文件路径")
    parser.add_argument("--output", type=str, required=True, 
                        help="集成结果输出文件路径")
    parser.add_argument("--hate-priority", action="store_true", default=True,
                        help="是否优先保留带hate标记的四元组")
    parser.add_argument("--nonhate-threshold", type=float, default=0.6,
                        help="非仇恨四元组的软投票保留阈值(0.0-1.0)")
    parser.add_argument("--seed", type=int, default=42,
                        help="随机数种子，用于软投票决策")
    
    args = parser.parse_args()
    
    start_time = time.time()
    logger.info(f"开始执行集成处理...")
    logger.info(f"读取模型1预测: {args.file1}")
    logger.info(f"读取模型2预测: {args.file2}")
    
    # 读取两个模型的预测结果
    try:
        with open(args.file1, encoding='utf-8') as f1, open(args.file2, encoding='utf-8') as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()
            
        if len(lines1) != len(lines2):
            raise ValueError(f"两个文件行数不一致: {len(lines1)} vs {len(lines2)}")
            
        logger.info(f"共读取 {len(lines1)} 条测试样本")
        
        # 存储集成后的结果
        ensemble_results = []
        quad_stats = {"common": 0, "hate_preserved": 0, "nonhate_preserved": 0, "nonhate_filtered": 0}
        
        # 逐行处理预测结果
        for i, (line1, line2) in enumerate(zip(lines1, lines2)):
            # 解析两个模型的预测四元组
            quads1 = parse_quadruples(line1)
            quads2 = parse_quadruples(line2)
            
            # 应用集成策略
            ensembled_quads = ensemble_predictions(
                quads1, quads2,
                hate_priority=args.hate_priority,
                nonhate_threshold=args.nonhate_threshold,
                random_seed=args.seed + i  # 每行使用不同随机种子
            )
            
            # 收集统计信息
            common_count = len(set(quads1).intersection(set(quads2)))
            quad_stats["common"] += common_count
            
            # 差集统计
            unique_quads = set(quads1).symmetric_difference(set(quads2))
            for quad in unique_quads:
                hateful = quad[3].lower() in ("hate", "yes")
                if hateful and quad in ensembled_quads:
                    quad_stats["hate_preserved"] += 1
                elif not hateful and quad in ensembled_quads:
                    quad_stats["nonhate_preserved"] += 1
                elif not hateful and quad not in ensembled_quads:
                    quad_stats["nonhate_filtered"] += 1
            
            # 格式化输出并添加到结果列表
            ensemble_results.append(format_output(ensembled_quads))
            
            # 每1000条打印进度
            if (i + 1) % 1000 == 0:
                logger.info(f"已处理 {i + 1}/{len(lines1)} 条样本")
        
        # 将结果写入输出文件
        with open(args.output, "w", encoding='utf-8') as fw:
            fw.write("\n".join(ensemble_results))
        
        # 打印统计信息
        logger.info(f"集成完成，统计信息:")
        logger.info(f"- 两模型共同预测四元组: {quad_stats['common']}个")
        logger.info(f"- 保留的仇恨四元组: {quad_stats['hate_preserved']}个")
        logger.info(f"- 保留的非仇恨四元组: {quad_stats['nonhate_preserved']}个")
        logger.info(f"- 过滤的非仇恨四元组: {quad_stats['nonhate_filtered']}个")
        
        # 保留率统计
        if quad_stats["nonhate_preserved"] + quad_stats["nonhate_filtered"] > 0:
            nonhate_preserve_rate = quad_stats["nonhate_preserved"] / (quad_stats["nonhate_preserved"] + quad_stats["nonhate_filtered"])
            logger.info(f"- 非仇恨四元组实际保留率: {nonhate_preserve_rate:.4f} (目标阈值: {args.nonhate_threshold})")
        
        logger.info(f"结果已写入: {args.output}")
        logger.info(f"总耗时: {time.time() - start_time:.2f}秒")
        
    except Exception as e:
        logger.error(f"集成处理失败: {str(e)}")
        raise
    

if __name__ == "__main__":
    main()