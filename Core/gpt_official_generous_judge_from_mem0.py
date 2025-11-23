"""
🏛️ OFFICIAL GENEROUS GPT-4O-MINI JUDGE EVALUATION (Mem0 LoCoMo methodology)

Оценивает V4.26 results используя ОФИЦИАЛЬНЫЙ generous prompt из Mem0.

Источник: https://github.com/mem0ai/mem0/blob/main/evaluation/metrics/llm_judge.py

Usage:
    python3 eval_v4.26_official_generous_judge.py results/v4.26_gpt4mini_20251113_234633.json
"""

import json
import sys
import os
import requests
from tqdm import tqdm
from category_labels import label_for
import os

# === Helpers: .env OPENAI_API_KEY loader ===
def _load_openai_api_key():
    key=os.getenv('OPENAI_API_KEY','').strip()
    if key:
        return key
    try:
        import os as _os
        script_dir = _os.path.dirname(_os.path.abspath(__file__))
        env_path = _os.path.join(script_dir, '.env')
        if _os.path.exists(env_path):
            with open(env_path,'r',encoding='utf-8') as f:
                for line in f:
                    line=line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if line.startswith('OPENAI_API_KEY'):
                        _,val=line.split('=',1)
                        val=val.strip().strip('"\'')
                        if val:
                            return val
    except Exception:
        pass
    return ''


# === OFFICIAL MEM0 GENEROUS JUDGE PROMPT ===
ACCURACY_PROMPT = """
Your task is to label an answer to a question as 'CORRECT' or 'WRONG'. You will be given the following data:
    (1) a question (posed by one user to another user),
    (2) a 'gold' (ground truth) answer,
    (3) a generated answer
which you will score as CORRECT/WRONG.

The point of the question is to ask about something one user should know about the other user based on their prior conversations.
The gold answer will usually be a concise and short answer that includes the referenced topic, for example:
Question: Do you remember what I got the last time I went to Hawaii?
Gold answer: A shell necklace
The generated answer might be much longer, but you should be generous with your grading - as long as it touches on the same topic as the gold answer, it should be counted as CORRECT.

For time related questions, the gold answer will be a specific date, month, year, etc. The generated answer might be much longer or use relative time references (like "last Tuesday" or "next month"), but you should be generous with your grading - as long as it refers to the same date or time period as the gold answer, it should be counted as CORRECT. Even if the format differs (e.g., "May 7th" vs "7 May"), consider it CORRECT if it's the same date.

Now it's time for the real question:
Question: {question}
Gold answer: {gold_answer}
Generated answer: {generated_answer}

First, provide a short (one sentence) explanation of your reasoning, then finish with CORRECT or WRONG.
Do NOT include both CORRECT and WRONG in your response, or it will break the evaluation script.

Just return the label CORRECT or WRONG in a json format with the key as "label".
"""

# OpenAI API key: read from environment (no hardcode)
OPENAI_API_KEY = _load_openai_api_key()
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set (env or .env) for generous judge")


def call_gpt4_judge(question: str, gold_answer: str, generated_answer: str) -> dict:
    """Вызов GPT-4o-mini API с official generous prompt (retry/backoff)."""
    import time
    last_err = None
    for attempt in range(4):  # 1 + 3 ретрая
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "user",
                            "content": ACCURACY_PROMPT.format(
                                question=question,
                                gold_answer=gold_answer,
                                generated_answer=generated_answer
                            )
                        }
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.0,
                },
                timeout=30
            )
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                data = json.loads(content)
                label = data.get("label", "").upper()
                return {
                    "label": label,
                    "score": 1 if label == "CORRECT" else 0,
                    "reasoning": data.get("reasoning", content)
                }
            else:
                last_err = RuntimeError(f"OpenAI API error: {response.status_code}, {response.text}")
        except Exception as e:
            last_err = e
        # backoff
        time.sleep(2 * (attempt + 1))
    # если не удалось
    raise last_err if last_err else RuntimeError("Judge call failed")


def evaluate_results(results_file: str):
    """Оценка результатов с Official Generous GPT-4o-mini Judge"""

    print(f"\n{'='*80}")
    print(f"🏛️  OFFICIAL GENEROUS GPT-4o-mini JUDGE (Mem0 methodology)")
    print(f"{'='*80}")
    print(f"📁 File: {results_file}")
    print()

    # Загрузка результатов
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    all_results = data.get('results', [])
    # Фильтруем только Cat1-4 (без adversarial Cat5)
    results = [r for r in all_results if r.get('category', 0) in [1, 2, 3, 4]]
    print(f"📊 Total questions: {len(all_results)} (filtering Cat1-4 only: {len(results)})")
    print()

    # Оценка каждого вопроса
    correct_count = 0
    judge_results = []

    for i, item in enumerate(tqdm(results, desc="🔄 Judging (GENEROUS)", unit="q")):
        question = item['question']
        ground_truth = item['ground_truth']
        generated_answer = item['generated_answer']
        category = item.get('category', 0)

        # Вызываем Official Generous Judge
        judge_result = call_gpt4_judge(question, ground_truth, generated_answer)

        # Сохраняем результат
        judge_results.append({
            'question': question,
            'ground_truth': ground_truth,
            'generated_answer': generated_answer,
            'category': category,
            'judge_label': judge_result['label'],
            'judge_score': judge_result['score'],
            'judge_reasoning': judge_result.get('reasoning', ''),
        })

        if judge_result['score'] == 1:
            correct_count += 1

    # Вычисляем accuracy
    accuracy = correct_count / len(results) if results else 0.0

    # Breakdown по категориям
    cat_stats = {}
    for r in judge_results:
        cat = r['category']
        if cat not in cat_stats:
            cat_stats[cat] = {'correct': 0, 'total': 0}
        cat_stats[cat]['total'] += 1
        if r['judge_score'] == 1:
            cat_stats[cat]['correct'] += 1

    # Выводим результаты
    print()
    print(f"{'='*80}")
    print(f"📊 OFFICIAL GENEROUS JUDGE RESULTS (Cat1-4 only):")
    print(f"{'='*80}")
    print(f"✅ Correct: {correct_count}/{len(results)} = {accuracy:.1%}")
    print(f"❌ Wrong: {len(results) - correct_count}/{len(results)} = {(1-accuracy):.1%}")
    print()
    print(f"📋 BREAKDOWN BY CATEGORY (OFFICIAL labels):")
    for cat in sorted(cat_stats.keys()):
        s = cat_stats[cat]
        cat_acc = s['correct'] / s['total'] if s['total'] > 0 else 0
        print(f"  Category {cat} ({label_for(cat)}): {s['correct']}/{s['total']} = {cat_acc:.1%}")
    print()

    # Показываем неправильные ответы
    wrong_items = [r for r in judge_results if r['judge_score'] == 0]
    if wrong_items:
        print(f"❌ WRONG ANSWERS ({len(wrong_items)}):")
        print("-" * 80)
        for item in wrong_items:
            print(f"Q: {item['question']}")
            print(f"GT: {item['ground_truth']}")
            print(f"AI: {item['generated_answer'][:100]}...")
            print(f"Judge: {item['judge_label']}")
            print(f"Reasoning: {item['judge_reasoning'][:150]}...")
            print()

    # Сохраняем результаты
    output_file = results_file.replace('.json', '_generous_judged.json')
    category_breakdown_named = {str(cat): {**stats, 'label': label_for(cat)} for cat, stats in cat_stats.items()}

    output_data = {
        'source_file': results_file,
        'judge_model': 'gpt-4o-mini (GENEROUS - Mem0 official)',
        'judge_prompt': 'ACCURACY_PROMPT (generous grading)',
        'filter': 'Cat1-4 only (no adversarial Cat5)',
        'llm_judge_accuracy': accuracy,
        'llm_judge_correct': correct_count,
        'llm_judge_total': len(results),
        'category_breakdown': cat_stats,
        'category_breakdown_named': category_breakdown_named,
        'judge_results': judge_results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved to: {output_file}")
    print(f"{'='*80}")

    return accuracy, judge_results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 eval_v4.26_official_generous_judge.py <results_file.json>")
        print()
        print("Example:")
        print("  python3 eval_v4.26_official_generous_judge.py results/v4.26_gpt4mini_20251113_234633.json")
        sys.exit(1)

    results_file = sys.argv[1]
    evaluate_results(results_file)
