"""WhatsApp Web adapter using the owner's existing browser session.

Selectors are configurable because web UIs change. Recipient resolution is
still exact: the phone number embedded in the target URL must be the resolved
owner/customer number supplied by the runtime.
"""
from __future__ import annotations
from typing import Any
from pathlib import Path
from adapters.browser import BrowserAdapter, classify_manual_intervention
from core.limits import whatsapp_limits

ROOT = Path(__file__).resolve().parents[1]

def _whatsapp_limits() -> tuple[int, int]:
    limits = whatsapp_limits()
    return limits["max_bubbles"], limits["max_chars"]

class WhatsAppWeb:
    def __init__(self, browser: BrowserAdapter, *, message_box_selector='div[contenteditable="true"]', send_selector='button[aria-label*="Send"],button[aria-label*="Enviar"]', max_bubbles=None, max_chars_per_bubble=None):
        policy_bubbles, policy_chars = _whatsapp_limits()
        self.browser=browser; self.message_box_selector=message_box_selector; self.send_selector=send_selector
        self.max_bubbles=max(1,min(policy_bubbles,int(max_bubbles if max_bubbles is not None else policy_bubbles)))
        self.max_chars_per_bubble=max(120,min(policy_chars,int(max_chars_per_bubble if max_chars_per_bubble is not None else policy_chars)))

    def open_chat(self, phone:str)->dict[str,Any]:
        digits=''.join(ch for ch in str(phone) if ch.isdigit())
        if len(digits)<8: return {'status':'BLOCKED','reason':'invalid_phone'}
        url=f'https://web.whatsapp.com/send?phone={digits}'
        self.browser.goto(url); text=self.browser.read(); manual=classify_manual_intervention(text,url)
        if manual['manual_required']: return {'status':'BLOCKED','blocker':manual['blocker'],'url':url}
        return {'status':'READY','phone':digits,'url':url}

    def send(self, phone:str, bubbles:list[str], *, expected_phone:str)->dict[str,Any]:
        digits=''.join(ch for ch in str(phone) if ch.isdigit())
        expected=''.join(ch for ch in str(expected_phone) if ch.isdigit())
        if not expected or digits!=expected: return {'status':'BLOCKED','reason':'recipient_exact_match_failed'}
        if not isinstance(bubbles,list) or not bubbles: return {'status':'BLOCKED','reason':'empty_message_package'}
        if len(bubbles)>self.max_bubbles: return {'status':'BLOCKED','reason':'too_many_whatsapp_bubbles','max_bubbles':self.max_bubbles}
        if any(not isinstance(message,str) or not message.strip() for message in bubbles): return {'status':'BLOCKED','reason':'empty_or_invalid_bubble'}
        if any(len(message)>self.max_chars_per_bubble for message in bubbles):
            return {'status':'BLOCKED','reason':'bubble_exceeds_hard_character_limit','max_chars_per_bubble':self.max_chars_per_bubble,'bubble_lengths':[len(m) for m in bubbles]}
        opened=self.open_chat(digits)
        if opened['status']!='READY': return opened
        for message in bubbles:
            self.browser.type(self.message_box_selector,message)
            self.browser.press(self.message_box_selector,'Enter')
        final=self.browser.read(); manual=classify_manual_intervention(final)
        if manual['manual_required']: return {'status':'BLOCKED','blocker':manual['blocker']}
        return {'status':'SUCCESS','phone':digits,'bubbles_sent':len(bubbles),'evidence':{'chat_url':opened['url']}}
