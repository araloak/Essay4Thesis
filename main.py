from util import *
from essay4thesis_abs import *
from essay4thesis_intro import *
from best_of_N import best_of_N_candidates
# 加载提示词
sys_prompt_path = "prompts/sys_prompt1.txt"
essay4thesis_abs_prompt_path = "prompts/essay4thesis_前言_prompt.txt"
essay4thesis_intro_prompt_path = "prompts/essay4thesis_引言_prompt.txt"
essay4thesis_method_prompt_path = "prompts/essay4thesis_方法_prompt.txt"

# 加载额外内容
example_essay4thesis_abs_path = "data/thesis/example_essay4thesis_前言.txt"
example_essay4thesis_intro_path = "data/thesis/example_essay4thesis_引言.txt"
example_essay4thesis_method_path = "data/thesis/example_essay4thesis_方法.txt"

example_essay_intro_path = "data/essays/example_essay_intro.txt"
essay_intro_path = "data/essays/essay1/intro.txt"

output_dir = "data/thesis/第三章/方法/"
section_title = "【第三章 面向大模型幻觉的生成不确定性估计方法】"

if __name__ == "__main__":
    pass