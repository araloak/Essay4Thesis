from util import *
from best_of_N import best_of_N_candidates
import time
import os
# 加载提示词
sys_prompt_path = "prompts/sys_prompt1.txt"
method_prompt_path = "prompts/essay4thesis_方法_prompt.txt"

example_essay_method_path = "data/essays/example_essay_exp.txt"
example_essay4thesis_method_path = "data/thesis/example_essay4thesis_实验.txt"
example_essay4thesis_abs_path = "data/thesis/example_essay4thesis_前言.txt"

essay4thesis_abs_path = "data/thesis/第三章/前言/最佳.txt"
essay_method_dir = "data/essays/essay1/exps/"

output_dir = "data/thesis/第三章/实验/"
section_title = "【第三章 面向大模型幻觉的生成不确定性估计方法】"

def generate_essay4thesis_method_section(section_title, 
                                 sys_prompt_path,
                                 method_prompt_path,
                                 example_essay4thesis_abs_path, example_essay4thesis_method_path, example_essay_method_path,
                                 essay4thesis_abs_path,
                                 essay_method_section_path,
                                 output_path,
                                 model="dsr1"):
    """
    为论文撰写前言部分的摘要内容。
    """
    # 加载提示词
    sys_prompt = load_prompt(sys_prompt_path)
    write_prompt = load_prompt(method_prompt_path)

    # 加载参考内容
    example_essay4thesis_method_content = load_prompt(example_essay4thesis_method_path)
    example_essay4thesis_abs_content = load_prompt(example_essay4thesis_abs_path)
    example_essay_method_content = load_prompt(example_essay_method_path)

    essay_method_content = load_prompt(essay_method_section_path)
    essay4thesis_abs_content = load_prompt(essay4thesis_abs_path)
    
    # 替换 write_prompt 中的占位符
    write_prompt = write_prompt.replace("{章节名}", section_title)
    write_prompt = write_prompt.replace("{前言样例}", example_essay4thesis_abs_content)
    write_prompt = write_prompt.replace("{essay method 样例}", example_essay_method_content)
    write_prompt = write_prompt.replace("{对应【方法】写作样例}", example_essay4thesis_method_content)
    write_prompt = write_prompt.replace("{用户essay Method}", essay_method_content)
    write_prompt = write_prompt.replace("{用户前言}", essay4thesis_abs_content)


    # 构建消息
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": write_prompt}
    ]

    # 调用模型生成内容
    response = query_llm(messages, model=model)
    final_response = response
    if model in ["dsr1","gemini-2.5-pro","qwen3"]:
        save_to_file(response, output_path+"_带有思维链.txt")
        final_response = remove_think_chain(response)

    # 保存生成的内容
    save_to_file(final_response, output_path)

    print(f"生成的内容已保存到 {output_path}")
    return final_response

def generate_best_essay4thesis_method_section(
        section_title,
        sys_prompt_path,
        method_prompt_path,
        example_essay4thesis_abs_path,
        example_essay4thesis_method_path,
        example_essay_method_path,
        essay4thesis_abs_content,
        essay_method_section_path,
        output_dir,
        comparison_time=5):

    """
    从多个论文前言摘要候选项中挑选出最优的一个。
    """
    model_names = ["gemini-2.0-flash", "dsr1", "gpt-4.1", "dsv3", "qwen3", "gemini-2.5-pro"]
    candidates = []
    for model_name in model_names:
        candidate = generate_essay4thesis_method_section(
            section_title,
            sys_prompt_path,
            method_prompt_path,
            example_essay4thesis_abs_path,
            example_essay4thesis_method_path,
            example_essay_method_path,
            essay4thesis_abs_content,
            essay_method_section_path,
            output_dir + "候选" + model_name + ".txt",
            model=model_name
        )
        candidates.append(candidate)
        time.sleep(2)  # 增加延迟，避免请求过于频繁

    # 调用 best_of_N 进行候选内容对比
    best_candidate = best_of_N_candidates(
        candidates,
        sys_prompt_path,
        method_prompt_path,
        essay_method_section_path,
        comparison_time=comparison_time,
        model="dsr1"
    )

    # 保存最佳候选内容
    best_output_path = output_dir + "最佳.txt"
    save_to_file(best_candidate, best_output_path)

    print(f"最佳候选内容已保存到 {best_output_path}")
    return best_candidate

def generate_essay4thesis_method(
        section_title_param,
        sys_prompt_path_param,
        method_prompt_path_param,
        example_essay4thesis_abs_path_param,
        example_essay4thesis_method_path_param,
        example_essay_method_path_param,
        essay4thesis_abs_content_param,
        essay_method_dir_param,
        output_dir_param):

    for section_file_name in os.listdir(essay_method_dir_param):
        essay_method_section_path = os.path.join(essay_method_dir_param, section_file_name)

        # 创建子目录
        section_output_dir = os.path.join(output_dir_param, os.path.splitext(section_file_name)[0])
        os.makedirs(section_output_dir, exist_ok=True)

        #output_path = os.path.join(section_output_dir, section_file_name)
        generate_best_essay4thesis_method_section(
            section_title_param,
            sys_prompt_path_param,
            method_prompt_path_param,
            example_essay4thesis_abs_path_param,
            example_essay4thesis_method_path_param,
            example_essay_method_path_param,
            essay4thesis_abs_content_param,
            essay_method_section_path,
            section_output_dir+"/",
        )

    #return generate_best_essay4thesis_method_section

if __name__ == "__main__":
    generate_essay4thesis_method(
        section_title,
        sys_prompt_path,
        method_prompt_path,
        example_essay4thesis_abs_path,
        example_essay4thesis_method_path,
        example_essay_method_path,
        essay4thesis_abs_path,
        essay_method_dir,
        output_dir
    )