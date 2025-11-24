import os, re
import uuid
from util import query_llm, load_prompt, remove_think_chain, save_to_file
from collections import Counter

compare_prompt_path = "prompts/compare_candidates.txt"

def best_of_N_candidates(candidates, sys_prompt_path, writing_prompt_path, essay_content_path, comparison_time, model="dsv3"):
    """
    从多个写作候选项中挑选出最优的一个。

    参数：
        candidates (list): 写作候选项列表。
        sys_prompt_path (str): 系统提示词文件路径。
        writing_prompt_path (str): 写作提示词文件路径。
        comparison_time (int): 比较次数。
        model (str): 使用的模型。

    返回：
        str: 被选中的最优候选项。
    """
    # 加载系统提示词和写作提示词
    sys_prompt = load_prompt(sys_prompt_path)
    writing_prompt = load_prompt(writing_prompt_path)
    essay_content = load_prompt(essay_content_path)
    compare_prompt_template = load_prompt(compare_prompt_path)

    # 构建比较提示词
    candidates_text = "\n".join([f"Candidate {i+1}:\n{c}" for i, c in enumerate(candidates)])
    compare_prompt = compare_prompt_template.replace("{sys_prompt}", sys_prompt)
    compare_prompt = compare_prompt.replace("{writing_prompt}", writing_prompt)
    compare_prompt = compare_prompt.replace("{essay_content}", essay_content)
    compare_prompt = compare_prompt.replace("{candidates}", candidates_text)

    # 记录每次筛选的结果
    selection_results = []

    # 生成唯一的运行 ID
    run_id = str(uuid.uuid4())
    comparison_dir = f"data/backups/candidate_comparison/{run_id}"
    os.makedirs(comparison_dir, exist_ok=True)

    for _ in range(comparison_time):
        # 构建消息
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": compare_prompt}
        ]

        # 调用模型进行筛选
        response = query_llm(messages, model=model)
        final_response = response
        if model in ["dsr1","gemini-2.5-pro","qwen3"]:
            final_response = remove_think_chain(response)

        comparison_output_path = f"{comparison_dir}/comparison_{_ + 1}.txt"
        save_to_file(response, comparison_output_path)

        # 提取模型返回的编号
        if final_response:
            try:
                # 使用正则表达式提取数字
                match = re.search(r"\b\d+\b", final_response)
                if match:
                    selected_number = int(match.group())
                    if 1 <= selected_number <= len(candidates):
                        selection_results.append(selected_number)
                    else:
                        print(f"无效的编号: {selected_number}")
                else:
                    print(f"未找到有效的编号: {response}")
            except ValueError:
                print(f"无法解析模型返回的编号: {response}")
        else:
            print("模型未返回有效响应。")

    # 统计每个候选项被选中的次数
    most_common = Counter(selection_results).most_common(1)

    if most_common:
        best_candidate_index = most_common[0][0] - 1  # 转换为 0 索引
        return candidates[best_candidate_index]
    else:
        print("未能选出最优候选项。")
        return None
    
def load_and_compare_candidates(candidate_files,sys_prompt_path, writing_prompt_path, essay_content_path, best_output_path, model="dsr1"):
    candidates = []
    for file_path in candidate_files:
        with open(file_path, "r", encoding="utf-8") as file:
            candidates.append(file.read())

    # 调用 best_of_N 进行候选内容对比
    best_candidate = best_of_N_candidates(
        candidates,
        sys_prompt_path,
        writing_prompt_path,
        essay_content_path,
        comparison_time=5,
        model="dsr1",
    )

    # 保存最佳候选内容
    save_to_file(best_candidate, best_output_path)

    print(f"最佳候选内容已保存到 {best_output_path}")

def test_load_and_compare_candidates(section_title="第三章", subsection_title="引言"):
    candidate_files = [
        f"data/thesis/{section_title}/{subsection_title}/候选gemini-2.0-flash.txt",
        f"data/thesis/{section_title}/{subsection_title}/候选dsr1.txt",
        f"data/thesis/{section_title}/{subsection_title}/候选gpt-4.1.txt",
        f"data/thesis/{section_title}/{subsection_title}/候选dsv3.txt",
        f"data/thesis/{section_title}/{subsection_title}/候选gemini-2.5-pro.txt",
        f"data/thesis/{section_title}/{subsection_title}/候选qwen3.txt",
    ]
    best_output_path = f"data/thesis/{section_title}/{subsection_title}/最佳.txt"
    sys_prompt_path = "prompts/sys_prompt1.txt"

    # 前言 设置路径
    writing_prompt_path = "prompts/essay4thesis_前言_prompt.txt"
    essay_content_path = "data/essays/essay1/intro.txt"

    # 引言 设置路径
    writing_prompt_path = "prompts/essay4thesis_引言_prompt.txt"
    essay_content_path = "data/essays/essay1/intro.txt"

    load_and_compare_candidates(candidate_files, sys_prompt_path, writing_prompt_path, essay_content_path, best_output_path)

if __name__ == "__main__":
    test_load_and_compare_candidates()