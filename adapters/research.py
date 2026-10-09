"""Small browser research adapter. It uses the real browser session, not a fake web result."""
from __future__ import annotations
from dataclasses import dataclass
from urllib.parse import quote_plus
from typing import Any
from adapters.browser import BrowserAdapter, classify_manual_intervention

@dataclass
class ResearchResult:
    status: str
    query: str
    text: str = ''
    blocker: str | None = None
    evidence: dict[str,Any] | None = None

class BrowserResearcher:
    def __init__(self,browser:BrowserAdapter,search_template='https://www.google.com/search?q={query}'):
        self.browser=browser; self.search_template=search_template
    def search(self,query:str)->ResearchResult:
        self.browser.goto(self.search_template.format(query=quote_plus(query)))
        text=self.browser.read()
        manual=classify_manual_intervention(text)
        if manual['manual_required']:
            return ResearchResult('BLOCKED',query,blocker=manual['blocker'],evidence=manual)
        return ResearchResult('SUCCESS',query,text=text,evidence={'query':query,'search_template':self.search_template})
