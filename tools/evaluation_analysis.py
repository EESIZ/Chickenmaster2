#!/usr/bin/env python3
"""
Agent Evaluation Results Analysis

Analyzes collected evaluation results and produces rankings.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import statistics


RESULTS_DIR = Path("results/agent_evaluation")
DOCS_DIR = Path("documents/notes")
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def load_all_results() -> List[Dict[str, Any]]:
    """Load all evaluation results."""
    results = []
    for filepath in RESULTS_DIR.glob("*_*_*.json"):
        if filepath.name == "evaluation_prompts.md":
            continue
        with open(filepath) as f:
            results.append(json.load(f))
    return results


def calculate_weighted_score(metrics: Dict[str, float]) -> float:
    """Calculate weighted score using the aggregation formula."""
    # Weights from plan: 0.45 correctness, 0.20 quality, 0.15 time, 0.10 token, 0.10 constraint
    weights = {
        "correctness": 0.45,
        "quality": 0.20,
        "time": 0.15,
        "token_efficiency": 0.10,
        "constraint_adherence": 0.10,
    }
    
    # Normalize quality (0-5 -> 0-1)
    normalized_metrics = metrics.copy()
    if metrics.get("quality") is not None:
        normalized_metrics["quality"] = metrics["quality"] / 5.0
    
    # Calculate time score (T_min=2, T_max=20)
    if metrics.get("time_minutes") is not None:
        t = metrics["time_minutes"]
        time_score = max(0, min(1, (20 - t) / (20 - 2)))
        normalized_metrics["time"] = time_score
    
    # Calculate weighted sum
    score = 0.0
    for key, weight in weights.items():
        value = normalized_metrics.get(key)
        if value is not None:
            score += weight * value
    
    return score


def analyze_per_model(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze scores per model."""
    model_scores = defaultdict(list)
    
    for result in results:
        if result.get("status") != "completed":
            continue
        model = result["model"]
        score = calculate_weighted_score(result["metrics"])
        model_scores[model].append(score)
    
    rankings = {}
    for model, scores in model_scores.items():
        rankings[model] = {
            "mean_score": statistics.mean(scores) if scores else 0,
            "median_score": statistics.median(scores) if scores else 0,
            "std_dev": statistics.stdev(scores) if len(scores) > 1 else 0,
            "count": len(scores),
        }
    
    # Sort by mean score
    sorted_rankings = dict(sorted(rankings.items(), key=lambda x: x[1]["mean_score"], reverse=True))
    return sorted_rankings


def analyze_per_agent(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze best model per agent."""
    agent_model_scores = defaultdict(lambda: defaultdict(list))
    
    for result in results:
        if result.get("status") != "completed":
            continue
        agent = result["agent_name"]
        model = result["model"]
        score = calculate_weighted_score(result["metrics"])
        agent_model_scores[agent][model].append(score)
    
    best_models = {}
    for agent, model_scores in agent_model_scores.items():
        # Average scores per model for this agent
        avg_scores = {
            model: statistics.mean(scores)
            for model, scores in model_scores.items()
        }
        best_model = max(avg_scores.items(), key=lambda x: x[1])
        best_models[agent] = {
            "best_model": best_model[0],
            "best_score": best_model[1],
            "all_scores": avg_scores,
        }
    
    return best_models


def generate_korean_report(
    per_model: Dict[str, Any],
    per_agent: Dict[str, Any],
    results: List[Dict[str, Any]]
) -> str:
    """Generate Korean analysis report."""
    report = f"""# Agent 평가 결과 분석

**생성일**: {Path(__file__).stat().st_mtime}
**총 실행 수**: {len(results)}
**완료된 실행**: {sum(1 for r in results if r.get('status') == 'completed')}

---

## 1. 모델별 종합 순위

전체 16개 agent에서의 평균 성능 기준:

"""
    
    for i, (model, stats) in enumerate(per_model.items(), 1):
        report += f"### {i}위: {model}\n"
        report += f"- **평균 점수**: {stats['mean_score']:.3f}\n"
        report += f"- **중앙값**: {stats['median_score']:.3f}\n"
        report += f"- **표준편차**: {stats['std_dev']:.3f}\n"
        report += f"- **평가 횟수**: {stats['count']}\n\n"
    
    report += "---\n\n## 2. Agent별 최적 모델\n\n"
    report += "| Agent | 최적 모델 | 점수 |\n"
    report += "|-------|----------|------|\n"
    
    for agent, info in sorted(per_agent.items()):
        report += f"| `{agent}` | {info['best_model']} | {info['best_score']:.3f} |\n"
    
    report += "\n---\n\n## 3. 주요 발견사항\n\n"
    report += "### 모델 특성\n\n"
    
    # Analyze correctness rates
    correctness_by_model = defaultdict(list)
    for result in results:
        if result.get("status") == "completed":
            model = result["model"]
            correctness = result["metrics"].get("correctness", 0)
            correctness_by_model[model].append(correctness)
    
    report += "**정확도 (테스트 통과율)**:\n\n"
    for model in per_model.keys():
        if model in correctness_by_model:
            rate = statistics.mean(correctness_by_model[model]) * 100
            report += f"- {model}: {rate:.1f}%\n"
    
    report += "\n### Agent 특성\n\n"
    report += "(추가 분석 필요)\n\n"
    
    report += "---\n\n## 4. 권장사항\n\n"
    report += "1. **고성능 agent**: 최고 점수 모델 사용\n"
    report += "2. **비용 민감 agent**: 차선 모델 고려 (성능 trade-off 분석 필요)\n"
    report += "3. **재평가 필요**: 실패율이 높은 agent/model 조합\n\n"
    
    report += "---\n\n## 5. 다음 단계\n\n"
    report += "- [ ] 실패 케이스 상세 분석\n"
    report += "- [ ] Token 효율성 vs 품질 trade-off 분석\n"
    report += "- [ ] 프롬프트 개선 실험\n"
    report += "- [ ] Agent 설정 파일 업데이트\n"
    
    return report


def main():
    """Run analysis and generate reports."""
    print("📊 Loading results...")
    results = load_all_results()
    print(f"✅ Loaded {len(results)} results")
    
    if not results:
        print("❌ No results found. Run evaluation first.")
        return
    
    print("\n📈 Analyzing per-model performance...")
    per_model = analyze_per_model(results)
    
    print("📈 Analyzing per-agent best models...")
    per_agent = analyze_per_agent(results)
    
    print("\n📝 Generating Korean report...")
    report = generate_korean_report(per_model, per_agent, results)
    
    report_path = DOCS_DIR / "2026-01-16_agent_evaluation_results.md"
    with open(report_path, "w") as f:
        f.write(report)
    
    print(f"✅ Report saved: {report_path}")
    
    # Save JSON summary
    summary_path = RESULTS_DIR / "evaluation_summary.json"
    summary = {
        "timestamp": str(Path(__file__).stat().st_mtime),
        "total_results": len(results),
        "completed_results": sum(1 for r in results if r.get("status") == "completed"),
        "per_model_rankings": per_model,
        "per_agent_best_models": per_agent,
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"✅ Summary saved: {summary_path}")


if __name__ == "__main__":
    main()
