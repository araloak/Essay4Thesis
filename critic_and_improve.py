import os
import json
import time
from typing import Optional
from util import load_prompt, query_llm, remove_think_chain, parse_llm_json

# 简洁一致的实现，使用 4 空格缩进，避免重复定义
RETRY_COUNT = 3
RETRY_DELAY = 5

def critic(draft_text: str,
           essay_text: str,
           draft_example_text: str,
           draft_prompt :str,
           critic_prompt: str,
           system_prompt: str,
           model: str = 'dsr1',
           *,
           save_raw_path: Optional[str] = None,
           save_json_path: Optional[str] = None,
           save_review_path: Optional[str] = None,
           save_failed_path: Optional[str] = None) -> Optional[str]:
    """Call LLM as critic, parse JSON, save raw/json/review and return review text or None."""
    prompt_filled = critic_prompt.replace('{博士论文草稿}', draft_text)
    prompt_filled = prompt_filled.replace('{essay内容}', essay_text or '')
    prompt_filled = prompt_filled.replace('{参考博士论文模板}', draft_example_text or '')
    prompt_filled = prompt_filled.replace('{博士论文写作指令}', draft_prompt or '')

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt_filled},
    ]

    last_exc = None
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            resp = query_llm(messages, model=model)
            raw = str(resp) if resp is not None else ''

            if save_raw_path:
                try:
                    os.makedirs(os.path.dirname(save_raw_path), exist_ok=True)
                    with open(save_raw_path, 'w', encoding='utf-8') as f:
                        f.write(raw)
                except Exception:
                    pass

            parsed = parse_llm_json(raw, save_failed_path=save_failed_path)

            if save_json_path:
                try:
                    os.makedirs(os.path.dirname(save_json_path), exist_ok=True)
                    with open(save_json_path, 'w', encoding='utf-8') as f:
                        json.dump(parsed, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass

            review = None
            if isinstance(parsed, dict):
                review = parsed.get('review')

            if save_review_path and review is not None:
                try:
                    os.makedirs(os.path.dirname(save_review_path), exist_ok=True)
                    with open(save_review_path, 'w', encoding='utf-8') as f:
                        f.write(review)
                except Exception:
                    pass

            return review
        except Exception as e:
            last_exc = e
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY)
                continue
            if save_json_path:
                try:
                    os.makedirs(os.path.dirname(save_json_path), exist_ok=True)
                    with open(save_json_path, 'w', encoding='utf-8') as f:
                        json.dump({'__parse_error__': str(last_exc)}, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            return None


def improve(draft_text: str,
            essay_text: str,
            essay4thesis_abs: str,
            critique_text: str,
            improve_prompt: str,
            system_prompt: str,
            model: str = 'dsr1',
            *,
            save_raw_path: Optional[str] = None,
            save_json_path: Optional[str] = None,
            save_revised_path: Optional[str] = None,
            save_failed_path: Optional[str] = None) -> Optional[str]:
    """Call LLM as improver, parse JSON, save raw/json/revised and return revised text or None."""
    prompt_filled = improve_prompt.replace('{原始博士论文草稿}', draft_text)
    prompt_filled = prompt_filled.replace('{批评意见}', critique_text or '')
    prompt_filled = prompt_filled.replace('{博士论文前言}', essay4thesis_abs or '')
    prompt_filled = prompt_filled.replace('{essay内容}', essay_text or '')

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt_filled},
    ]

    last_exc = None
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            resp = query_llm(messages, model=model)
            raw = str(resp) if resp is not None else ''

            if save_raw_path:
                try:
                    os.makedirs(os.path.dirname(save_raw_path), exist_ok=True)
                    with open(save_raw_path, 'w', encoding='utf-8') as f:
                        f.write(raw)
                except Exception:
                    pass

            cleaned = remove_think_chain(raw)
            parsed = parse_llm_json(cleaned, save_failed_path=save_failed_path)

            if save_json_path:
                try:
                    os.makedirs(os.path.dirname(save_json_path), exist_ok=True)
                    with open(save_json_path, 'w', encoding='utf-8') as f:
                        json.dump(parsed, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass

            revised = None
            if isinstance(parsed, dict) and 'revised_text' in parsed:
                revised = parsed.get('revised_text')
            else:
                revised = cleaned

            if save_revised_path and revised is not None:
                try:
                    os.makedirs(os.path.dirname(save_revised_path), exist_ok=True)
                    with open(save_revised_path, 'w', encoding='utf-8') as f:
                        f.write(revised)
                except Exception:
                    pass

            return revised
        except Exception as e:
            last_exc = e
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY)
                continue
            if save_json_path:
                try:
                    os.makedirs(os.path.dirname(save_json_path), exist_ok=True)
                    with open(save_json_path, 'w', encoding='utf-8') as f:
                        json.dump({'__parse_error__': str(last_exc)}, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            return None


def _next_run_dir(base_dir: str, draft_path: str) -> str:
    os.makedirs(base_dir, exist_ok=True)
    max_n = 0
    for name in os.listdir(base_dir):
        if name.startswith('run_'):
            try:
                n = int(name.split('_', 1)[1].split('_')[0])
                if n > max_n:
                    max_n = n
            except Exception:
                continue

    # 提取 draft_path 的最后三层子目录作为 suffix
    suffix = "_".join(os.path.normpath(draft_path).split(os.sep)[-4:])
    next_n = max_n + 1
    run_dir = os.path.join(base_dir, f'run_{next_n}_{suffix}')
    os.makedirs(run_dir, exist_ok=True)
    return run_dir


def iterate_critic_improve(draft_path: str,
                           essay_path: str,
                           essay4thesis_abs_path: str,
                           draft_prompt_path: str,
                           draft_example_path: str,
                           rounds: int = 3,
                           model: str = 'dsr1',
                           critic_prompt_path: str = 'prompts/critic.txt',
                           improve_prompt_path: str = 'prompts/improve.txt',
                           system_prompt_path: str = 'prompts/sys_prompt1.txt') -> str:
    critic_prompt = load_prompt(critic_prompt_path)
    improve_prompt = load_prompt(improve_prompt_path)
    draft_prompt = load_prompt(draft_prompt_path)
    system_prompt = load_prompt(system_prompt_path)

    draft_text = load_prompt(draft_path)
    draft_example_text = load_prompt(draft_example_path)
    essay_text = load_prompt(essay_path) if os.path.exists(essay_path) else ''
    essay4thesis_abs_text = load_prompt(essay4thesis_abs_path)

    run_dir = _next_run_dir('data/backups/critic_improve', draft_path)
    current = draft_text

    for r in range(1, rounds + 1):
        crit_raw = os.path.join(run_dir, f'critique_round_{r}_raw.txt')
        crit_json = os.path.join(run_dir, f'critique_round_{r}.json')
        crit_review = os.path.join(run_dir, f'critique_round_{r}_review.txt')
        crit_failed = os.path.join(run_dir, f'critique_round_{r}_failed_raw.txt')

        review = critic(current, essay_text, draft_example_text, draft_prompt, critic_prompt, system_prompt, model=model, save_raw_path=crit_raw, save_json_path=crit_json, save_review_path=crit_review, save_failed_path=crit_failed)

        imp_raw = os.path.join(run_dir, f'draft_round_{r}_after_raw.txt')
        imp_json = os.path.join(run_dir, f'draft_round_{r}_after.json')
        imp_txt = os.path.join(run_dir, f'draft_round_{r}_after.txt')
        imp_failed = os.path.join(run_dir, f'draft_round_{r}_after_failed_raw.txt')

        revised = improve(current, essay_text, essay4thesis_abs_text, review or '', improve_prompt, system_prompt, model=model,
                         save_raw_path=imp_raw, save_json_path=imp_json, save_revised_path=imp_txt,
                         save_failed_path=imp_failed)

        if revised:
            current = revised

    final = os.path.join(run_dir, 'final_draft.txt')
    try:
        with open(final, 'w', encoding='utf-8') as f:
            f.write(current)
    except Exception:
        pass

    return run_dir


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--draft', type=str, default='data/thesis/第三章/方法/subsec2/最佳.txt')
    parser.add_argument('--essay', type=str, default='data/essays/essay1/method/subsec2.txt')

    parser.add_argument('--draft_prompt', type=str, default='prompts/essay4thesis_方法_prompt.txt')
    parser.add_argument('--draft_example', type=str, default='data/thesis/example_essay4thesis_方法.txt')
    parser.add_argument('--essay4thesis_abs', type=str, default='data/thesis/第三章/方法/overview/最佳.txt')
    parser.add_argument('--rounds', type=int, default=10)
    parser.add_argument('--model', type=str, default='dsr1')
    args = parser.parse_args()
    iterate_critic_improve(args.draft, args.essay, args.essay4thesis_abs, args.draft_prompt, args.draft_example, rounds=args.rounds, model=args.model)
