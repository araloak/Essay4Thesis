from util import *
import time
from best_of_N import best_of_N_candidates
# 加载提示词
sys_prompt_path = "prompts/sys_prompt1.txt"
essay4thesis_intro_prompt_path = "prompts/essay4thesis_引言_prompt.txt"

example_essay4thesis_intro_path = "data/thesis/example_essay4thesis_引言.txt"
example_essay_intro_path = "data/essays/example_essay_intro.txt"
essay_intro_path = "data/essays/essay1/intro.txt"

model = "dsr1"
output_dir = "data/thesis/第三章/引言/"
section_title = "【第三章 面向大模型幻觉的生成不确定性估计方法】"

def generate_essay4thesis_intro(section_title, sys_prompt_path, essay4thesis_intro_prompt_path, example_essay4thesis_intro_path, example_essay_intro_path, essay_intro_path, output_path, model="dsr1"):
    """
    为论文撰写引言部分的摘要内容。
    """
    # 加载提示词
    sys_prompt = load_prompt(sys_prompt_path)
    write_prompt = load_prompt(essay4thesis_intro_prompt_path)

    # 加载参考内容
    example_essay4thesis_intro_content = load_prompt(example_essay4thesis_intro_path)
    example_essay_intro_content = load_prompt(example_essay_intro_path)
    essay_intro_content = load_prompt(essay_intro_path)
    
    # 替换 write_prompt 中的占位符
    write_prompt = write_prompt.replace("{章节名}", section_title)
    write_prompt = write_prompt.replace("{essay intro 样例}", example_essay_intro_content)
    write_prompt = write_prompt.replace("{对应【引言】写作样例}", example_essay4thesis_intro_content)
    write_prompt = write_prompt.replace("{用户essay intro}", essay_intro_content)


    # 构建消息
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": write_prompt}
    ]

    # 调用模型生成内容
    response = query_llm(messages, model="gemini-2.0-flash")
    final_response = response
    if model in ["dsr1","gemini-2.5-pro","qwen3"]:
        save_to_file(response, output_path+"_带有思维链.txt")
        final_response = remove_think_chain(response)

    # 保存生成的内容
    save_to_file(final_response, output_path)

    print(f"生成的内容已保存到 {output_path}")
    return final_response

def generate_best_essay4thesis_intro(section_title, sys_prompt_path, essay4thesis_intro_prompt_path, example_essay4thesis_intro_path, example_essay_intro_path, essay_intro_path, comparison_time=5, model="dsr1"):

    """
    从多个论文前言摘要候选项中挑选出最优的一个。
    """
    model_name_list =  ["gemini-2.0-flash", "dsr1","gpt-4.1", "dsv3", "qwen3","gemini-2.5-pro"]
    candidate_essay4thesis_intro_list = []
    for model in model_name_list:
        candidate_essay4thesis_intro = generate_essay4thesis_intro(
            section_title,
            sys_prompt_path,
            essay4thesis_intro_prompt_path,
            example_essay4thesis_intro_path,
            example_essay_intro_path,
            essay_intro_path,
            output_dir+"候选"+str(model)+".txt",
            model=model
        )
        candidate_essay4thesis_intro_list.append(candidate_essay4thesis_intro)
        time.sleep(2)  # 增加延迟，避免请求过于频繁


    # 调用 best_of_N 进行候选内容对比
    best_candidate = best_of_N_candidates(
        candidate_essay4thesis_intro_list,
        sys_prompt_path,
        essay4thesis_intro_prompt_path,
        essay_intro_path,
        comparison_time=5,
        model="dsr1"
    )

    # 保存最佳候选内容
    best_output_path = output_dir + "最佳.txt"
    save_to_file(best_candidate, best_output_path)

    print(f"最佳候选内容已保存到 {best_output_path}")
    return best_candidate

if __name__ == "__main__":
    generate_best_essay4thesis_intro(section_title, sys_prompt_path, essay4thesis_intro_prompt_path, example_essay4thesis_intro_path, example_essay_intro_path,essay_intro_path)