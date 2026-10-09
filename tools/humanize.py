#!/usr/bin/env python3
"""Final communication QA; it cannot manufacture a conversation plan."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'config'/'humanizer.json').read_text(encoding='utf-8'))

SEMANTIC_RESIDUE = [
    r"^obrigad[oa] (?:pelo|pela) (?:áudio|audio|texto|mensagem)",
    r"^entendi(?:\b|[.!])",
    r"^ótimo(?:\b|[.!])",
    r"^perfeito(?:\b|[.!])",
    r"^claro(?:\b|[.!])",
    r"^com certeza(?:\b|[.!])",
    r"^fico à disposição(?:\b|[.!])",
]
CORPORATE = set(CFG.get('corporate_phrases', [])) | {
    'solução personalizada','solução estratégica','experiência personalizada',
    'gostaria de apresentar','estou à disposição','fico à disposição',
    'nesse sentido','oportunidade incrível','atendimento personalizado',
}


def analyze(text:str, recent_openings=None):
    recent_openings=recent_openings or []
    lower=text.lower().strip()
    issues=[]; hints=[]
    if any(re.match(p, lower, re.I) for p in SEMANTIC_RESIDUE):
        issues.append('stock_acknowledgment_opener'); hints.append('não use confirmação automática como conteúdo da primeira bolha')
    hits=[p for p in CORPORATE if p in lower]
    if hits:
        issues.append('corporate_or_marketing_phrase'); hints.append('troque linguagem institucional por algo concreto do caso')
    residue=[p for p in CFG.get('chatbot_residue',[]) if p in lower]
    if residue:
        issues.append('chatbot_residue'); hints.append('retire fechamento automático de assistente')
    if text.count(':') > max(1, round(len(text)/250)):
        issues.append('excessive_colons'); hints.append('use pontuação natural em conversa comum')
    sentences=[s for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s]
    if len(sentences)>8 and len(text)<900:
        issues.append('overexplaining'); hints.append('reduza até restar somente o que muda o próximo passo')
    if len(text)>1100:
        issues.append('chat_too_long'); hints.append('quebre o raciocínio antes de enviar; não conte a venda inteira')
    if text.count('?')>=4:
        issues.append('question_stacking'); hints.append('faça uma pergunta principal por vez')
    if re.search(r'!!+|\?{3,}', text):
        issues.append('excessive_punctuation'); hints.append('reduza pontuação de efeito')
    if recent_openings:
        first = re.sub(r'^["\' ]+','', lower.split('.')[0]).strip()[:60]
        if any(first==str(x).lower() for x in recent_openings[-3:]):
            issues.append('repeated_opening'); hints.append('não reutilize a mesma abertura automaticamente')
    # Detect simple “acknowledgement + acknowledgement + question” formula.
    if sum(bool(re.search(p, lower, re.I)) for p in SEMANTIC_RESIDUE) >= 2:
        issues.append('stacked_acknowledgements'); hints.append('elimine confirmações que não carregam a conversa')
    return {'passes':not issues,'issue_count':len(issues),'issues':issues,'hints':hints,'metrics':{'chars':len(text),'sentences':len(sentences),'questions':text.count('?')}}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--text',required=True); ap.add_argument('--recent-openings',default='[]'); args=ap.parse_args()
    print(json.dumps(analyze(args.text,json.loads(args.recent_openings)),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
