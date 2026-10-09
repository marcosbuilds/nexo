"""Execute declarative browser operations and stop only on real manual boundaries."""
from __future__ import annotations
from typing import Any
from adapters.browser import BrowserAdapter, classify_manual_intervention

class BrowserOperator:
    def __init__(self, browser: BrowserAdapter): self.browser=browser

    def run(self, steps:list[dict[str,Any]])->dict[str,Any]:
        evidence=[]
        for index,step in enumerate(steps,1):
            page_text=''
            try: page_text=self.browser.read()
            except Exception: pass
            manual=classify_manual_intervention(page_text)
            if manual['manual_required']:
                return {'status':'BLOCKED','blocker':manual['blocker'],'failed_step':index,'evidence':evidence}
            kind=step.get('type')
            if kind=='goto': self.browser.goto(step['url'])
            elif kind=='click': self.browser.click(step['selector'])
            elif kind=='type': self.browser.type(step['selector'],step.get('text',''))
            elif kind=='press': self.browser.press(step['selector'],step['key'])
            elif kind=='read': page_text=self.browser.read(); evidence.append({'step':index,'type':'read','chars':len(page_text)})
            elif kind=='screenshot': evidence.append({'step':index,'path':self.browser.screenshot(step['path'])})
            else: return {'status':'FAILED','blocker':'UNSUPPORTED_BROWSER_STEP','failed_step':index}
            evidence.append({'step':index,'type':kind,'status':'ok'})
        final_text=''
        try: final_text=self.browser.read()
        except Exception: pass
        manual=classify_manual_intervention(final_text)
        if manual['manual_required']:
            return {'status':'BLOCKED','blocker':manual['blocker'],'evidence':evidence}
        return {'status':'SUCCESS','evidence':evidence}
