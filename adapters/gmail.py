"""Gmail Web adapter. Real account/session state comes from the persistent browser profile."""
from __future__ import annotations
from typing import Any
from adapters.browser import BrowserAdapter, classify_manual_intervention

class GmailWeb:
    def __init__(self,browser:BrowserAdapter): self.browser=browser
    def open(self)->dict[str,Any]:
        url='https://mail.google.com/mail/u/0/#inbox'; self.browser.goto(url); text=self.browser.read(); manual=classify_manual_intervention(text,url)
        if manual['manual_required']: return {'status':'BLOCKED','blocker':manual['blocker'],'url':url}
        return {'status':'READY','url':url,'body_chars':len(text)}
