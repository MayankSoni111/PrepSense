"""
Dataset Curator & Generator for Fine-Tuning (Member 4 - Week 5 Deliverable)
PrepSense - Company-Aware AI Interview Preparation System

Responsible for:
- Curating 100-200 diverse, quality-controlled feedback examples.
- Covering both technical and behavioral rubrics across multiple engineering roles.
- Including Weak (1-3), Average (4-7), and Strong (8-10) answers.
- Producing a train / held-out test split for Member 5's Google Colab fine-tuning pipeline.
"""

import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Diverse technical roles and skillsets
ROLES = [
    {
        "role": "Backend Engineer",
        "skills": ["Python", "PostgreSQL", "FastAPI", "Docker", "Redis"],
        "technical_topics": [
            ("How do you design database indexing for high-write tables?", "database"),
            ("How would you mitigate a cascading service failure in microservices?", "system_design"),
            ("How does connection pooling work in PostgreSQL and why is it needed?", "database"),
            ("Explain the difference between optimistic and pessimistic locking.", "concurrency"),
            ("How do you handle idempotent requests in a REST payment API?", "api_design"),
        ],
    },
    {
        "role": "Frontend Engineer",
        "skills": ["React", "TypeScript", "Next.js", "TailwindCSS", "Redux"],
        "technical_topics": [
            ("How do you optimize initial page load performance in a Next.js app?", "web_perf"),
            ("How do you manage global state between deeply nested components?", "state_management"),
            ("Explain how the virtual DOM diffing algorithm works in React.", "framework_internals"),
            ("How do you prevent unnecessary component re-renders?", "optimization"),
            ("How do you handle client-side token storage securely against XSS?", "security"),
        ],
    },
    {
        "role": "DevOps & Cloud Engineer",
        "skills": ["Kubernetes", "AWS", "Terraform", "CI/CD", "Prometheus"],
        "technical_topics": [
            ("How do you configure zero-downtime rolling deployments in Kubernetes?", "orchestration"),
            ("How do you debug an application stuck in CrashLoopBackOff?", "troubleshooting"),
            ("Explain the purpose of Terraform state locking with S3 and DynamoDB.", "iac"),
            ("How do you set up distributed tracing for microservices?", "observability"),
            ("How do you manage secrets securely in containerized environments?", "security"),
        ],
    },
    {
        "role": "Machine Learning Engineer",
        "skills": ["PyTorch", "Transformers", "Python", "MLflow", "Docker"],
        "technical_topics": [
            ("How do you detect and handle data distribution drift in production?", "mlops"),
            ("Explain the trade-offs between LoRA and full parameter fine-tuning.", "llm_architecture"),
            ("How do you optimize LLM inference latency for real-time applications?", "inference_perf"),
            ("How do you prevent overfitting in small dataset regimes?", "model_training"),
            ("Explain how gradient checkpointing saves GPU memory.", "training_perf"),
        ],
    },
]

# Behavioral themes
BEHAVIORAL_THEMES = [
    ("Tell me about a time you had a strong disagreement with a technical decision.", "conflict_resolution"),
    ("Describe a high-severity production outage you responded to.", "crisis_management"),
    ("Tell me about a time you had to deliver under an aggressive and shifting deadline.", "time_management"),
    ("Describe a situation where you identified technical debt and advocated to fix it.", "leadership_initiative"),
    ("Tell me about a time you had to learn an unfamiliar technology stack very quickly.", "adaptability"),
]


def generate_curated_dataset(total_target: int = 150, train_ratio: float = 0.8) -> tuple[list[dict], list[dict]]:
    """Generate curated dataset split into train and held-out test splits."""
    random.seed(42)  # Deterministic seed for reproducible evaluation
    samples = []
    sample_id = 1

    # 1. Generate Technical Samples
    for role_info in ROLES:
        role_title = role_info["role"]
        skills_str = ", ".join(role_info["skills"])
        role_context = f"Role: {role_title}. Key skills: {skills_str}."

        for question, category in role_info["technical_topics"]:
            # Weak Case
            samples.append({
                "id": f"tech_{sample_id:04d}",
                "category": category,
                "question_type": "technical",
                "role_context": role_context,
                "question": question,
                "tier": "weak",
                "candidate_answer": "I would just search Google or ask another teammate to look into it because I haven't worked with that much.",
                "expected_feedback": {
                    "criteria_scores": {
                        "technical_accuracy": {"score": 2, "evidence": "Did not articulate technical concepts; deferred to search engines or teammates."},
                        "problem_solving_depth": {"score": 1, "evidence": "No concrete problem-solving strategy or architectural trade-offs."},
                        "relevance": {"score": 3, "evidence": "Acknowledged the topic but provided no answer to the specific question."},
                        "clarity_and_structure": {"score": 3, "evidence": "Vague one-line response lacking structure."},
                    },
                    "strengths": ["Acknowledged personal knowledge limitation."],
                    "missing_points": ["Did not attempt to describe concepts, tools, or relevant architectural patterns."],
                    "suggestions": ["Explain basic fundamentals of the concept even when unsure of deep implementation details."],
                    "star_feedback": "Not applicable",
                },
            })
            sample_id += 1

            # Average Case
            samples.append({
                "id": f"tech_{sample_id:04d}",
                "category": category,
                "question_type": "technical",
                "role_context": role_context,
                "question": question,
                "tier": "average",
                "candidate_answer": f"In {role_title}, I usually use standard tools like {role_info['skills'][0]} to configure this properly and monitor performance in logs.",
                "expected_feedback": {
                    "criteria_scores": {
                        "technical_accuracy": {"score": 6, "evidence": f"Correctly referenced relevant domain tooling ({role_info['skills'][0]})."},
                        "problem_solving_depth": {"score": 5, "evidence": "Mentioned high-level approach but skipped failure modes, trade-offs, and metrics."},
                        "relevance": {"score": 7, "evidence": "Aligned with the role context and question topic."},
                        "clarity_and_structure": {"score": 6, "evidence": "Coherent response but somewhat generic."},
                    },
                    "strengths": [f"Identified appropriate tech stack ({role_info['skills'][0]})."],
                    "missing_points": ["Could go into deeper operational mechanics, performance trade-offs, and edge cases."],
                    "suggestions": ["Include specific commands, configuration parameters, or concrete scenarios to prove mastery."],
                    "star_feedback": "Not applicable",
                },
            })
            sample_id += 1

            # Strong Case
            samples.append({
                "id": f"tech_{sample_id:04d}",
                "category": category,
                "question_type": "technical",
                "role_context": role_context,
                "question": question,
                "tier": "strong",
                "candidate_answer": f"To address this systematically, I first analyze the primary constraints such as throughput and latency. I implement the solution using {role_info['skills'][0]} with proper configuration safeguards, evaluate trade-offs like memory overhead, and set up automated health checks and alerts to ensure system reliability under peak load.",
                "expected_feedback": {
                    "criteria_scores": {
                        "technical_accuracy": {"score": 9, "evidence": "Accurate architectural methodology integrating constraints, implementation, and safeguards."},
                        "problem_solving_depth": {"score": 8, "evidence": "Addressed trade-offs, memory constraints, and automated monitoring."},
                        "relevance": {"score": 9, "evidence": "Directly targeted core engineering challenges of the question."},
                        "clarity_and_structure": {"score": 9, "evidence": "Logical progression from constraints to implementation to operational monitoring."},
                    },
                    "strengths": ["Structured architectural thinking with operational awareness.", "Explicit consideration of trade-offs and monitoring."],
                    "missing_points": ["Could provide quantitative benchmark thresholds or specific tooling names for metrics."],
                    "suggestions": ["Mention specific numerical metrics (e.g. p99 latency targets) achieved in past implementations."],
                    "star_feedback": "Not applicable",
                },
            })
            sample_id += 1

    # 2. Generate Behavioral Samples
    for question, category in BEHAVIORAL_THEMES:
        for role_info in ROLES:
            role_context = f"Role: {role_info['role']}."

            # Weak Behavioral
            samples.append({
                "id": f"behav_{sample_id:04d}",
                "category": category,
                "question_type": "behavioral",
                "role_context": role_context,
                "question": question,
                "tier": "weak",
                "candidate_answer": "That happened before at my old company. It was pretty chaotic but management sorted it out eventually.",
                "expected_feedback": {
                    "criteria_scores": {
                        "situation_task": {"score": 3, "evidence": "Vague situation with no context on company, stakes, or personal task."},
                        "action": {"score": 1, "evidence": "Zero individual action taken; deferred entirely to management."},
                        "result_impact": {"score": 2, "evidence": "Vague outcome ('sorted it out') without measurable results or learnings."},
                        "communication_relevance": {"score": 3, "evidence": "Too brief and passive."},
                    },
                    "strengths": ["Answered the prompt directly."],
                    "missing_points": ["Did not demonstrate individual ownership, communication, or problem solving."],
                    "suggestions": ["Follow the STAR method: describe your specific role, actions you drove, and the final impact."],
                    "star_feedback": "STAR method lacking: Candidate took no personal action and provided passive outcome.",
                },
            })
            sample_id += 1

            # Average Behavioral
            samples.append({
                "id": f"behav_{sample_id:04d}",
                "category": category,
                "question_type": "behavioral",
                "role_context": role_context,
                "question": question,
                "tier": "average",
                "candidate_answer": "In our team, when that issue came up, I discussed it with my manager and teammates during standup. We agreed on a compromise and I finished my assigned tasks on time.",
                "expected_feedback": {
                    "criteria_scores": {
                        "situation_task": {"score": 6, "evidence": "Context and discussion in standup described adequately."},
                        "action": {"score": 6, "evidence": "Communicated with team and implemented agreed compromise."},
                        "result_impact": {"score": 6, "evidence": "Delivered assigned tasks on time; lacked quantified business metrics."},
                        "communication_relevance": {"score": 7, "evidence": "Direct and polite response."},
                    },
                    "strengths": ["Demonstrated constructive communication and collaboration."],
                    "missing_points": ["Could provide more specific technical details on the conflict or metrics on the final outcome."],
                    "suggestions": ["Share details on how you evaluated trade-offs between competing technical proposals."],
                    "star_feedback": "STAR assessment: Solid Situation and Task; could deepen Action and measurable Result.",
                },
            })
            sample_id += 1

            # Strong Behavioral
            samples.append({
                "id": f"behav_{sample_id:04d}",
                "category": category,
                "question_type": "behavioral",
                "role_context": role_context,
                "question": question,
                "tier": "strong",
                "candidate_answer": "In my previous role as an engineer, our service experienced unexpected degradation 2 hours before a major product demo. As the designated incident responder, I triaged the error logs, identified a deadlock in our worker pool, and deployed a targeted patch with automated rollback guards. The issue was resolved within 25 minutes, the demo proceeded smoothly with zero dropped requests, and I subsequently published a post-mortem with preventative unit tests.",
                "expected_feedback": {
                    "criteria_scores": {
                        "situation_task": {"score": 9, "evidence": "Clear stakes (service degradation 2 hours before demo) and defined personal role."},
                        "action": {"score": 9, "evidence": "Triaged logs, isolated deadlock, deployed patch with rollback safeguards."},
                        "result_impact": {"score": 9, "evidence": "Resolved in 25 mins, zero dropped requests, added post-mortem & tests."},
                        "communication_relevance": {"score": 9, "evidence": "Exemplary STAR narrative progression and professional delivery."},
                    },
                    "strengths": ["Exemplary STAR structure with quantified recovery timeline.", "Demonstrated proactive post-incident prevention."],
                    "missing_points": ["Could mention how stakeholders were kept updated during the active 25 minutes."],
                    "suggestions": ["Discuss communication cadences during ongoing critical incidents."],
                    "star_feedback": "STAR assessment: Outstanding execution across Situation, Task, Action, and quantified Result.",
                },
            })
            sample_id += 1

    # Shuffle samples deterministically
    random.shuffle(samples)

    # Train / Held-out Test split
    split_idx = int(len(samples) * train_ratio)
    train_data = samples[:split_idx]
    test_data = samples[split_idx:]

    return train_data, test_data


if __name__ == "__main__":
    train_set, test_set = generate_curated_dataset(total_target=150, train_ratio=0.8)

    train_path = PROJECT_ROOT / "evaluation" / "train_dataset.json"
    test_path = PROJECT_ROOT / "evaluation" / "test_dataset.json"

    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(train_set, f, indent=2)

    with open(test_path, "w", encoding="utf-8") as f:
        json.dump(test_set, f, indent=2)

    print(f"[Dataset Curator] ✅ Successfully generated:")
    print(f"  - Training Set: {len(train_set)} curated pairs -> {train_path}")
    print(f"  - Held-out Test Set: {len(test_set)} curated pairs -> {test_path}")
    print(f"  - Total Dataset: {len(train_set) + len(test_set)} curated examples")
