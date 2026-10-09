import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness import decide as liveness
from communicate import decide as communication
from operate import preflight
from session import SessionState, decide as session
from search import plan as seek


def test_authorized_connected_account_executes_without_confirmation():
    out = preflight({"action":"send_message","account_permission":True,"status":"READY"})
    assert out["decision"] == "ALLOW_EXECUTE"
    assert out["next_action"] == "EXECUTE_NOW"


def test_empty_queue_generates_demand_before_waiting():
    out = session(SessionState(False,0,0,0,0,0,0,0,0,False,False,False,continuous_mode=True))
    assert out["decision"] == "CONTINUE_WORK_SEEKING"


def test_work_seek_diversifies_sources():
    out = seek({"recent_sources":["freelance_marketplaces","freelance_marketplaces"]})
    sources = [a.get("source") for a in out["actions"] if a.get("source")]
    assert sources and all(s != "freelance_marketplaces" for s in sources[:2])


def test_no_response_is_a_valid_communication_decision():
    out = communication({"response_needed":False})
    assert out["decision"] == "NO_SEND"


def test_whatsapp_is_packaged_into_natural_bubbles():
    draft = "A primeira parte explica o resultado que podemos entregar. A segunda parte delimita o que está incluído no trabalho. A terceira parte pede apenas o próximo passo para seguir com isso."
    out = communication({"response_needed":True,"draft":draft,"channel":"whatsapp"})
    assert out["decision"] == "SEND"
    assert 1 <= out["count"] <= 3


def test_liveness_beats_confirmation():
    out = liveness({"requested":True,"authorized":True,"capability_available":True,"preconditions_met":True,"status":"READY","confirmation_requests":5})
    assert out["decision"] == "EXECUTE_NOW"
