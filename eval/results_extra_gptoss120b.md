# Evaluation results

_Generated on 2026-11-06 09:38_

## Retrieval: hit rate@5 on 4 questions

| Mode | Hit rate | Avg latency |
|---|---|---|
| dense | 3/4 (75%) | 11 ms |
| sparse | 3/4 (75%) | 43 ms |
| hybrid | 3/4 (75%) | 70 ms |

## Agent: end-to-end accuracy

LLM: `groq` (`openai/gpt-oss-120b`)

| Question type | Correct answers | Correct tool routing | Median latency |
|---|---|---|---|
| sql | 5/5 (100%) | 5/5 (100%) | 1.3 s |
| rag | 3/4 (75%) | 3/4 (75%) | 16.1 s |
| mixed | 2/3 (67%) | 1/3 (33%) | 6.7 s |
| all | 10/12 (83%) | 9/12 (75%) | 12.6 s |

### Failed questions (to analyse)

- **rag_10** Which host country lost the decisive last match of a World Cup at home against its South American neighbour? — tools: ['query_database'] — answer: 'Brazil.'
- **mix_03** Who won Euro 2004, and how many matches did they win at that tournament? — tools: [] — answer: "AGENT ERROR: Error code: 429 - {'error': {'message': 'Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01m6qz7n2zej8s3wqngmqqcegx` service tier `on_demand` on tokens per minute "
