"""Tests for MedrxivRetriever."""

import requests
from omegaconf import open_dict
from types import SimpleNamespace

from zotero_arxiv_daily.retriever.medrxiv_retriever import MedrxivRetriever


def test_medrxiv_server_attribute(config):
    with open_dict(config.source):
        config.source.medrxiv = {"category": ["neurology"]}
    retriever = MedrxivRetriever(config)
    assert retriever.server == "medrxiv"


def test_medrxiv_pdf_url(config):
    with open_dict(config.source):
        config.source.medrxiv = {"category": ["neurology"]}
    retriever = MedrxivRetriever(config)
    paper = retriever.convert_to_paper({
        "doi": "10.1101/2026.03.01.999",
        "title": "A medrxiv paper",
        "authors": "Smith, J.",
        "abstract": "Abstract.",
        "version": "1",
    })
    assert "medrxiv.org" in paper.pdf_url
    assert paper.source == "medrxiv"


def test_medrxiv_retrieve_uses_target_date(config, monkeypatch):
    payload = {
        "messages": [{"status": "ok"}],
        "collection": [
            {
                "doi": "10.1101/2026.04.07.999",
                "title": "Older med paper",
                "authors": "Smith, J.",
                "abstract": "Abstract.",
                "category": "neurology",
                "date": "2026-04-07",
                "version": "1",
            },
            {
                "doi": "10.1101/2026.04.08.999",
                "title": "Target med paper",
                "authors": "Smith, J.",
                "abstract": "Abstract.",
                "category": "neurology",
                "date": "2026-04-08",
                "version": "1",
            },
        ],
    }

    def _patched(url, **kw):
        resp = SimpleNamespace(status_code=200, raise_for_status=lambda: None)
        resp.json = lambda: payload
        return resp

    monkeypatch.setattr(requests, "get", _patched)

    with open_dict(config.source):
        config.source.medrxiv = {"category": ["neurology"]}
        config.source.target_date = "2026-04-08"

    retriever = MedrxivRetriever(config)
    papers = retriever.retrieve_papers()

    assert len(papers) == 1
    assert papers[0].title == "Target med paper"
