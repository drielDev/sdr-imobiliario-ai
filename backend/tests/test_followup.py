from datetime import datetime, timedelta

from app.qualificacao.followup import FollowUpService
from app.qualificacao.models import DadosExtraidosLead, StatusLead
from app.qualificacao.qualificacao import atualizar_lead, criar_lead
from app.qualificacao.repository import InMemoryLeadRepository


class RelogioFalso:

    def __init__(self, inicio: datetime):
        self._agora = inicio

    def agora(self) -> datetime:
        return self._agora

    def avancar(self, **kwargs) -> None:
        self._agora += timedelta(**kwargs)


class CanalFalso:

    def __init__(self):
        self.mensagens: list[tuple[str, str]] = []

    def enviar(self, lead, mensagem: str) -> None:
        self.mensagens.append((lead.id, mensagem))


def _setup():

    relogio = RelogioFalso(datetime(2026, 1, 1, 10, 0))
    repo = InMemoryLeadRepository()
    service = FollowUpService(repo, relogio)

    return repo, relogio, service


def test_lead_recente_nao_e_elegivel_para_followup():

    repo, relogio, service = _setup()
    criar_lead(repo, "lead-1", canal="whatsapp", contato="123", relogio=relogio)

    assert service.leads_elegiveis_agora() == []


def test_lead_inativo_apos_intervalo_fica_elegivel():

    repo, relogio, service = _setup()
    criar_lead(repo, "lead-1", canal="whatsapp", contato="123", relogio=relogio)

    relogio.avancar(minutes=61)

    elegiveis = service.leads_elegiveis_agora()

    assert len(elegiveis) == 1
    assert elegiveis[0].numero_tentativa == 1
    assert elegiveis[0].mensagem_sugerida


def test_registrar_tentativa_incrementa_e_muda_status():

    repo, relogio, service = _setup()
    criar_lead(repo, "lead-1", canal="whatsapp", contato="123", relogio=relogio)
    relogio.avancar(minutes=61)

    lead = service.registrar_tentativa("lead-1")

    assert lead.tentativas_followup == 1
    assert lead.status == StatusLead.EM_FOLLOWUP


def test_tentativas_esgotadas_marcam_lead_como_inativo():

    repo, relogio, service = _setup()
    criar_lead(repo, "lead-1", canal="whatsapp", contato="123", relogio=relogio)

    for _ in range(3):
        relogio.avancar(days=3)
        service.registrar_tentativa("lead-1")

    lead = repo.obter("lead-1")

    assert lead.status == StatusLead.INATIVO
    assert lead.tentativas_followup == 3


def test_lead_que_volta_a_responder_sai_do_followup():

    repo, relogio, service = _setup()
    criar_lead(repo, "lead-1", canal="whatsapp", contato="123", relogio=relogio)
    relogio.avancar(minutes=61)
    service.registrar_tentativa("lead-1")

    lead = repo.obter("lead-1")
    assert lead.status == StatusLead.EM_FOLLOWUP

    lead = atualizar_lead(repo, "lead-1", DadosExtraidosLead(regiao="Moema"), relogio=relogio)

    assert lead.tentativas_followup == 0
    assert lead.status != StatusLead.EM_FOLLOWUP
    assert service.leads_elegiveis_agora() == []


def test_executar_followup_envia_pelo_canal_e_registra_tentativa():

    repo, relogio, service = _setup()
    criar_lead(repo, "lead-1", canal="whatsapp", contato="123", relogio=relogio)
    relogio.avancar(minutes=61)

    canal = CanalFalso()
    lead = service.executar_followup("lead-1", canal)

    assert lead.tentativas_followup == 1
    assert canal.mensagens[0][0] == "lead-1"
