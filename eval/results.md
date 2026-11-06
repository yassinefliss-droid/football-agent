# Evaluation results

_Generated on 2026-11-06 08:38_

## Retrieval: hit rate@5 on 9 questions

| Mode | Hit rate | Avg latency |
|---|---|---|
| dense | 8/9 (89%) | 37 ms |
| sparse | 9/9 (100%) | 143 ms |
| hybrid | 9/9 (100%) | 174 ms |

## Agent: end-to-end accuracy

LLM: `ollama` (`qwen2.5:7b`)

| Question type | Correct answers | Correct tool routing | Median latency |
|---|---|---|---|
| sql | 8/15 (53%) | 15/15 (100%) | 32.0 s |
| rag | 8/9 (89%) | 8/9 (89%) | 101.8 s |
| mixed | 0/2 (0%) | 2/2 (100%) | 34.6 s |
| all | 16/26 (62%) | 25/26 (96%) | 42.1 s |

### Failed questions (to analyse)

- **sql_01** How many matches has Tunisia won, drawn and lost in total? — tools: ['query_database'] — answer: 'Tunisia has won 334 matches, drawn 191 matches, and lost 158 matches in total.'
- **sql_04** How many matches were played at the 2022 FIFA World Cup? — tools: ['query_database'] — answer: '164 matches were played at the 2022 FIFA World Cup.'
- **sql_05** How many matches were played at the 2026 FIFA World Cup? — tools: ['query_database'] — answer: '120 matches were played at the 2026 FIFA World Cup.'
- **sql_06** Which national team has played the most international matches, and how many? — tools: ['query_database'] — answer: 'The national team that has played the most international matches is Brazil, with a total of 618 matches played.'
- **sql_12** How many own goals have been scored in FIFA World Cup matches? — tools: ['query_database'] — answer: 'In FIFA World Cup matches, there have been 505 own goals scored.'
- **sql_14** Which team has won the most matches at FIFA World Cups, and how many? — tools: ['query_database'] — answer: 'The team that has won the most matches at FIFA World Cups is "Draw" with 2096 wins. This statistic includes draws being counted as wins for the purposes of this query.'
- **sql_15** How many penalties were scored at the 2022 FIFA World Cup (excluding shootouts)? — tools: ['query_database'] — answer: 'At the 2022 FIFA World Cup, 39 penalties were scored by players from various teams.'
- **rag_06** How many teams took part in the first Africa Cup of Nations in 1957? — tools: ['query_database'] — answer: 'In the first African Cup of Nations in 1957, 2 teams participated.'
- **mix_01** How many goals were scored at the 2018 World Cup, and which country hosted it? — tools: ['query_database'] — answer: 'In the 2018 FIFA World Cup, a total of 64 goals were scored, and the tournament was hosted by Russia.'
- **mix_02** How many matches were played at the 2022 World Cup, and which country hosted it? — tools: ['query_database'] — answer: 'A total of 78 matches were played at the 2022 FIFA World Cup, which was hosted by Qatar.'
