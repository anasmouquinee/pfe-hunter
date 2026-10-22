"""Cover letter and email body generator dynamically tailored to the offer's tech stack."""

import html
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import config
from src.models.offer import JobOffer
from src.utils.logger import logger

FRENCH_MONTHS = [
    "", "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]


def format_french_date(dt: Optional[datetime] = None) -> str:
    """Returns current date formatted in standard French correspondence format (e.g., '22 octobre 2026')."""
    now = dt or datetime.now()
    month_name = FRENCH_MONTHS[now.month] if 1 <= now.month <= 12 else str(now.month)
    return f"{now.day} {month_name} {now.year}"


class CoverLetterGenerator:
    """
    Generates personalized, high-converting application emails and formal cover letters
    (Lettres de Motivation) in both plain text and A4 print-ready HTML.
    """

    @staticmethod
    def generate_subject(offer: JobOffer) -> str:
        """Standardized professional email subject line."""
        role_label = offer.title if "pfe" in offer.title.lower() else f"Stage PFE -- {offer.title}"
        return f"Candidature {role_label} -- {config.candidate.full_name}"

    @staticmethod
    def _select_highlighted_projects(offer: JobOffer) -> list[tuple[str, str]]:
        """
        Dynamically selects the top 3 most relevant projects based on the offer's domain.
        Always includes the two flagship industrial experiences (COSUMAR, SEWS-CABINET)
        and tailors the leading engineering project (Lakehouse or Multi-Agent).
        """
        text = f"{offer.title} {offer.description}".lower()
        projects: list[tuple[str, str]] = []

        is_data_focused = any(kw in text for kw in ("data", "etl", "airflow", "kafka", "pipeline", "lakehouse", "sql"))

        if is_data_focused:
            projects.append((
                "Enterprise Media Lakehouse",
                "Plateforme distribuée de streaming et pipelines ETL avec Apache Airflow, Kafka, Docker Compose et architecture Medallion."
            ))
        else:
            projects.append((
                "AI Multi-Agent Orchestrator",
                "Framework d'agents autonomes, Vector Search RAG, intégration LangChain et API REST sous FastAPI."
            ))

        # Always highlight both industrial internships
        projects.append((
            "COSUMAR",
            "Stage ingénieur Data : Automatisation des flux de production, pipelines Python/SQL et dashboards de KPIs opérationnels."
        ))
        projects.append((
            "SEWS-CABINET",
            "Sumitomo Electric Group : Application industrielle SEWS Connect, modules temps réel WebRTC et architecture offline-first."
        ))

        return projects

    @classmethod
    def generate_body(cls, offer: JobOffer) -> str:
        """Generates dynamic French plain-text email body tailored to the company and role."""
        company = offer.company if offer.company else "votre entreprise"
        title = offer.title if offer.title else "Stage PFE"
        cand = config.candidate

        skills_text = ""
        if offer.matched_skills:
            top_skills = ", ".join(offer.matched_skills[:4])
            skills_text = f"notamment autour de technologies telles que {top_skills}, "

        projects = cls._select_highlighted_projects(offer)
        projects_str = "\n".join(f"- **{name}** : {desc}" for name, desc in projects)

        body = f"""Bonjour,

Je vous contacte afin de vous soumettre ma candidature pour l'opportunité de **{title}** au sein de **{company}**.

Actuellement élève-ingénieur en 5ème année à l'{cand.school}, spécialisé en **{cand.specialization}**, je suis activement à la recherche d'un **Stage de Projet de Fin d'Études (PFE) de 4 à 6 mois** disponible pour l'année 2026 à Casablanca (ou en mode hybride/remote).

Mon parcours m'a permis de développer une solide expertise pratique {skills_text}consolidée par mes réalisations et projets d'ingénierie :
{projects_str}

Intégrer {company} représente pour moi l'opportunité idéale d'apporter ma rigueur, mes compétences techniques et de m'investir pleinement au sein de vos chantiers technologiques.

Vous trouverez ci-joint mon Curriculum Vitae détaillé pour complément d'information. Je serais ravi d'échanger avec vous lors d'un entretien à votre convenance.

Dans l'attente de votre retour, je vous prie d'agréer mes salutations les plus respectueuses.

Cordialement,

{cand.full_name}
Élève-Ingénieur en 5ème Année -- {cand.specialization} ({cand.school})
Téléphone : {cand.phone} | Email : {cand.email}
LinkedIn : {cand.linkedin_url}
GitHub : {cand.github_url}
Portfolio : {cand.portfolio_url}
"""
        return body

    @classmethod
    def generate_html_body(cls, offer: JobOffer) -> str:
        """Generates a beautifully styled, mobile-responsive HTML email body."""
        company = html.escape(offer.company if offer.company else "votre entreprise")
        title = html.escape(offer.title if offer.title else "Stage PFE")
        cand = config.candidate

        skills_text = ""
        if offer.matched_skills:
            top_skills = ", ".join(offer.matched_skills[:4])
            skills_text = f"notamment autour de technologies clés telles que <strong>{html.escape(top_skills)}</strong>, "

        projects = cls._select_highlighted_projects(offer)
        projects_li = "\n".join(
            f"<li style='margin-bottom: 8px;'><strong style='color: #1e3a8a;'>{html.escape(name)}</strong> : {html.escape(desc)}</li>"
            for name, desc in projects
        )

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1f2937; background-color: #ffffff; padding: 20px;">
  <p>Bonjour,</p>

  <p>Je vous contacte afin de vous soumettre ma candidature pour l'opportunité de <strong>{title}</strong> au sein de <strong>{company}</strong>.</p>

  <p>Actuellement élève-ingénieur en 5ème année à l'<strong>{html.escape(cand.school)}</strong>, spécialisé en <strong>{html.escape(cand.specialization)}</strong>, je suis activement à la recherche d'un <strong>Stage de Projet de Fin d'Études (PFE) de 4 à 6 mois</strong> disponible pour l'année 2026 à Casablanca (ou en mode hybride/remote).</p>

  <p>Mon parcours m'a permis de développer une solide expertise pratique {skills_text}consolidée par des réalisations concrètes :</p>

  <ul style="padding-left: 20px; color: #374151;">
    {projects_li}
  </ul>

  <p>Intégrer <strong>{company}</strong> représente pour moi l'opportunité idéale d'apporter ma rigueur et de participer activement à vos chantiers technologiques.</p>

  <p>Vous trouverez ci-joint mon <strong>Curriculum Vitae détaillé</strong> pour complément d'information. Je serais ravi d'échanger avec vous lors d'un entretien à votre convenance.</p>

  <p>Dans l'attente de votre retour, je vous prie d'agréer mes salutations les plus respectueuses.</p>

  <br>
  <div style="border-top: 2px solid #e5e7eb; padding-top: 14px; margin-top: 20px;">
    <p style="margin: 0; font-size: 16px; font-weight: bold; color: #111827;">{html.escape(cand.full_name)}</p>
    <p style="margin: 2px 0; font-size: 13px; color: #4b5563;">Élève-Ingénieur en 5ème Année -- {html.escape(cand.specialization)}</p>
    <p style="margin: 2px 0; font-size: 13px; color: #6b7280;">{html.escape(cand.school)}</p>
    <p style="margin: 6px 0 0 0; font-size: 13px;">
      📞 {html.escape(cand.phone)} &nbsp;|&nbsp; ✉️ <a href="mailto:{html.escape(cand.email)}" style="color: #2563eb;">{html.escape(cand.email)}</a>
    </p>
    <p style="margin: 4px 0 0 0; font-size: 13px;">
      🔗 <a href="{html.escape(cand.linkedin_url)}" style="color: #2563eb;">LinkedIn</a> &nbsp;|&nbsp;
      💻 <a href="{html.escape(cand.github_url)}" style="color: #2563eb;">GitHub</a> &nbsp;|&nbsp;
      🌐 <a href="{html.escape(cand.portfolio_url)}" style="color: #2563eb;">Portfolio</a>
    </p>
  </div>
</body>
</html>"""

    @classmethod
    def generate_formal_letter_text(cls, offer: JobOffer) -> str:
        """
        Generates a formal, executive French cover letter (Lettre de Motivation) in plain text,
        specifically tailored to the company, technical stack, and pre-embauche requirements.
        """
        cand = config.candidate
        company = offer.company if offer.company else "Votre Entreprise"
        title = offer.title if offer.title else "Stage PFE"
        date_str = format_french_date()

        combined_text = f"{offer.company} {offer.title} {offer.description}".lower()
        is_pre_embauche = any(k in combined_text for k in ("pré-embauche", "pre-embauche", "pré embauche", "pre embauche"))
        is_coface = "coface" in combined_text
        is_datalab = "datalab" in combined_text

        # Recipient block
        if is_coface and is_datalab:
            recipient_lines = (
                "À l'attention de l'Équipe Recrutement & de la Direction du DataLab\n"
                "Coface Maroc / DataLab\n"
                "Casablanca Finance City (CFC), Casablanca, Maroc"
            )
        elif is_coface:
            recipient_lines = (
                "À l'attention de la Direction des Ressources Humaines\n"
                "Coface Maroc\n"
                "Casablanca Finance City (CFC), Casablanca, Maroc"
            )
        else:
            recipient_lines = (
                f"À l'attention de la Direction des Ressources Humaines & de l'Équipe Technique\n"
                f"{company}\n"
                f"{offer.location or 'Casablanca, Maroc'}"
            )
        # Subject line formatted without duplicate prefixes or suffixes

        clean_title = title.strip()
        if clean_title.lower().startswith("stages pfe"):
            clean_title = "Stage PFE" + clean_title[10:]
        has_pre_in_title = any(p in clean_title.lower() for p in ("pré-embauche", "pre-embauche", "pré embauche", "pre embauche"))
        pre_suffix = " (Perspective de Pré-Embauche)" if (is_pre_embauche and not has_pre_in_title) else ""

        if clean_title.lower().startswith("stage pfe"):
            objet = f"Objet : Candidature au {clean_title}{pre_suffix}"
        else:
            objet = f"Objet : Candidature au Stage PFE 2026/2027 – {clean_title}{pre_suffix}"

        intro_role = "Stage PFE 2026/2027 – DataLab (Pré-Embauche)" if (is_coface and is_datalab) else clean_title



        # Company-specific motivation paragraph
        if is_coface and is_datalab:
            company_section = (
                "Leader mondial de l'assurance-crédit et acteur de premier plan dans l'intelligence économique "
                "et la gestion des risques d'entreprise, Coface place la valorisation de la donnée au cœur de sa "
                "stratégie décisionnelle. Les chantiers d'envergure portés par votre DataLab — modélisation prédictive "
                "du risque de défaillance, scoring financier d'entreprises et automatisation de pipelines analytiques massifs — "
                "correspondent très exactement au domaine d'excellence dans lequel je souhaite m'investir et apporter une valeur "
                "ajoutée concrète et mesurable."
            )
        elif is_coface:
            company_section = (
                "Leader mondial de l'assurance-crédit et référence incontournable de l'analyse des risques interentreprises, "
                "Coface s'appuie sur une culture poussée de l'excellence et de l'innovation analytique. Intégrer vos équipes "
                "représente pour moi l'opportunité idéale de mettre mes compétences en ingénierie de données et en modélisation "
                "au service de vos enjeux stratégiques."
            )
        else:
            skills_hint = ""
            if offer.matched_skills:
                skills_hint = f" en phase avec vos exigences ({', '.join(offer.matched_skills[:4])})"
            company_section = (
                f"Rejoindre {company} représente une étape déterminante dans mon parcours d'ingénieur. Votre dynamisme, "
                f"vos chantiers technologiques et l'expertise de vos équipes constituent l'environnement stimulant au sein "
                f"duquel je souhaite mettre à profit mes compétences techniques{skills_hint} et ma capacité d'innovation."
            )

        # Pre-embauche commitment paragraph
        if is_pre_embauche:
            commitment_text = (
                "La perspective de pré-embauche stipulée dans votre offre répond parfaitement à mon projet professionnel : "
                "mon ambition est de m'investir sur le long terme au sein de vos équipes, de monter rapidement en compétence sur "
                "vos métiers et de pérenniser ma contribution à vos succès au-delà du stage de fin d'études."
            )
        else:
            commitment_text = (
                "Rigoureux, autonome et force de proposition, je suis animé par la volonté de m'investir pleinement sur vos "
                "projets et de collaborer efficacement avec l'ensemble des parties prenantes techniques et métiers."
            )

        letter = f"""{cand.full_name}
Élève-Ingénieur en 5ème Année – {cand.specialization}
{cand.school}
Casablanca, Maroc
Tél : {cand.phone} | Email : {cand.email}
LinkedIn : {cand.linkedin_url} | Portfolio : {cand.portfolio_url}

{recipient_lines}

Fait à Casablanca, le {date_str}

{objet}

Madame, Monsieur,

Actuellement élève-ingénieur en 5ème année à l'{cand.school}, spécialisé en {cand.specialization}, je vous adresse avec un vif enthousiasme ma candidature pour l'opportunité de {intro_role} au sein de {company}.

{company_section}


Mon cursus académique d'excellence et mes réalisations d'ingénierie m'ont permis de développer une double compétence pointue en Data Engineering et en Intelligence Artificielle :
- Data Engineering & Streaming : Conception et déploiement d'une plateforme Enterprise Media Lakehouse (architecture Medallion Bronze/Silver/Gold) orchestrant plus de 100 000 flux de données quotidiens via des DAGs Apache Airflow, Apache Kafka et conteneurisation Docker.
- IA Avancée & Systèmes Intelligents : Conception d'un framework d'agents autonomes (Multi-Agent Orchestrator), intégration de pipelines RAG (Retrieval-Augmented Generation) avec recherche vectorielle sémantique et moteurs de graphes de connaissances (Neo4j / LLM).

Cette expertise théorique est renforcée par des expériences industrielles probantes :
- Chez COSUMAR (Stage Ingénieur Data) : Conception et automatisation de pipelines ETL en Python et SQL pour plus de 20 KPIs opérationnels, réduisant le temps de génération des rapports d'activité de 75% et le temps de diagnostic des anomalies opérationnelles de 30%.
- Chez SEWS-CABINET (Sumitomo Electric Group) : Développement d'applications industrielles collaboratives avec modules temps réel et architectures offline-first résilientes.

{commitment_text}

Disponible dès le début de l'année 2026 pour une durée de 4 à 6 mois, je serais honoré d'échanger avec vous lors d'un entretien afin de vous exposer de vive voix la pertinence de mon profil et ma motivation à rejoindre {company}.

Vous remerciant par avance de l'attention que vous porterez à ma candidature, je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations les plus distinguées.

{cand.full_name}
Élève-Ingénieur en 5ème Année – {cand.specialization}
{cand.school}
"""
        return letter

    @classmethod
    def generate_formal_letter_html(cls, offer: JobOffer) -> str:
        """
        Generates an executive, print-ready A4 HTML cover letter with clean styling,
        interactive toolbar (1-click PDF print, text copying), and professional letterhead.
        """
        cand = config.candidate
        company = offer.company if offer.company else "Votre Entreprise"
        title = offer.title if offer.title else "Stage PFE"
        date_str = format_french_date()

        combined_text = f"{offer.company} {offer.title} {offer.description}".lower()
        is_pre_embauche = any(k in combined_text for k in ("pré-embauche", "pre-embauche", "pré embauche", "pre embauche"))
        is_coface = "coface" in combined_text
        is_datalab = "datalab" in combined_text

        # Recipient HTML
        if is_coface and is_datalab:
            recipient_html = """
              <strong>À l'attention de l'Équipe Recrutement & de la Direction du DataLab</strong><br>
              <span style="color: #1e3a8a; font-weight: 600;">Coface Maroc / DataLab</span><br>
              Casablanca Finance City (CFC)<br>
              Casablanca, Maroc
            """
        elif is_coface:
            recipient_html = """
              <strong>À l'attention de la Direction des Ressources Humaines</strong><br>
              <span style="color: #1e3a8a; font-weight: 600;">Coface Maroc</span><br>
              Casablanca Finance City (CFC)<br>
              Casablanca, Maroc
            """
        else:
            recipient_html = f"""
              <strong>À l'attention de la Direction des Ressources Humaines & de l'Équipe Technique</strong><br>
              <span style="color: #1e3a8a; font-weight: 600;">{html.escape(company)}</span><br>
              {html.escape(offer.location or 'Casablanca, Maroc')}
            """

        # Subject line and role formatting without duplicate prefixes
        clean_title = title.strip()
        if clean_title.lower().startswith("stages pfe"):
            clean_title = "Stage PFE" + clean_title[10:]
        has_pre_in_title = any(p in clean_title.lower() for p in ("pré-embauche", "pre-embauche", "pré embauche", "pre embauche"))
        pre_suffix = " (Perspective de Pré-Embauche)" if (is_pre_embauche and not has_pre_in_title) else ""

        if clean_title.lower().startswith("stage pfe"):
            objet_title = f"{clean_title}{pre_suffix}"
        else:
            objet_title = f"Stage PFE 2026/2027 – {clean_title}{pre_suffix}"

        intro_role = "Stage PFE 2026/2027 – DataLab (Pré-Embauche)" if (is_coface and is_datalab) else clean_title


        # Pre-embauche badge
        pre_badge = '<span class="badge badge-accent">Perspective de Pré-Embauche</span>' if is_pre_embauche else ""


        # Company paragraph
        if is_coface and is_datalab:
            company_p = (
                "Leader mondial de l'assurance-crédit et acteur de premier plan dans l'intelligence économique "
                "et la gestion des risques d'entreprise, Coface place la valorisation de la donnée au cœur de sa "
                "stratégie décisionnelle. Les chantiers d'envergure portés par votre <strong>DataLab</strong> — "
                "<strong>modélisation prédictive du risque de défaillance</strong>, <strong>scoring financier d'entreprises</strong> "
                "et <strong>automatisation de pipelines analytiques massifs</strong> — correspondent très exactement au domaine "
                "d'excellence dans lequel je souhaite m'investir et apporter une valeur ajoutée concrète et mesurable."
            )
        elif is_coface:
            company_p = (
                "Leader mondial de l'assurance-crédit et référence incontournable de l'analyse des risques interentreprises, "
                "Coface s'appuie sur une culture poussée de l'excellence et de l'innovation analytique. Intégrer vos équipes "
                "représente pour moi l'opportunité idéale de mettre mes compétences en ingénierie de données et en modélisation "
                "au service de vos enjeux stratégiques."
            )
        else:
            skills_hint = ""
            if offer.matched_skills:
                skills_hint = f" en phase avec vos exigences clés (<em>{html.escape(', '.join(offer.matched_skills[:4]))}</em>)"
            company_p = (
                f"Rejoindre <strong>{html.escape(company)}</strong> représente une étape déterminante dans mon parcours d'ingénieur. "
                f"Votre dynamisme, vos chantiers technologiques et l'expertise de vos équipes constituent l'environnement stimulant au sein "
                f"duquel je souhaite mettre à profit mes compétences techniques{skills_hint} et ma capacité d'innovation."
            )

        # Commitment paragraph
        if is_pre_embauche:
            commitment_p = (
                "La <strong>perspective de pré-embauche</strong> stipulée dans votre offre répond parfaitement à mon projet professionnel : "
                "mon ambition est de m'investir sur le long terme au sein de vos équipes, de monter rapidement en compétence sur vos métiers "
                "et de pérenniser ma contribution à vos succès au-delà du stage de fin d'études."
            )
        else:
            commitment_p = (
                "Rigoureux, autonome et force de proposition, je suis animé par la volonté de m'investir pleinement sur vos projets "
                "et de collaborer efficacement avec l'ensemble des parties prenantes techniques et métiers."
            )

        raw_text_for_copy = cls.generate_formal_letter_text(offer).replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")

        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Lettre de Motivation - {html.escape(cand.full_name)} - {html.escape(company)}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {{
      --primary: #1e3a8a;
      --primary-light: #eff6ff;
      --accent: #0284c7;
      --text-main: #1f2937;
      --text-muted: #4b5563;
      --border: #e5e7eb;
      --bg-page: #f8fafc;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background-color: var(--bg-page);
      color: var(--text-main);
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
      padding: 24px 16px;
    }}

    /* Toolbar for interactive view */
    .toolbar {{
      max-width: 840px;
      margin: 0 auto 20px auto;
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px 20px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }}

    .toolbar-info {{
      font-size: 14px;
      color: var(--text-muted);
    }}

    .toolbar-info strong {{
      color: var(--primary);
    }}

    .toolbar-actions {{
      display: flex;
      gap: 10px;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background-color: var(--primary);
      color: #ffffff;
      border: none;
      padding: 9px 16px;
      font-size: 13.5px;
      font-weight: 600;
      border-radius: 8px;
      cursor: pointer;
      text-decoration: none;
      transition: background 0.15s ease, transform 0.1s ease;
    }}

    .btn:hover {{
      background-color: #1e40af;
      transform: translateY(-1px);
    }}

    .btn-secondary {{
      background-color: #f3f4f6;
      color: #374151;
      border: 1px solid #d1d5db;
    }}

    .btn-secondary:hover {{
      background-color: #e5e7eb;
      color: #111827;
    }}

    /* A4 Document Container */
    .a4-container {{
      max-width: 840px;
      margin: 0 auto;
      background: #ffffff;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      padding: 56px 64px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.06);
    }}

    /* Header section */
    .letter-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 24px;
      padding-bottom: 24px;
      border-bottom: 2px solid var(--primary-light);
      margin-bottom: 24px;
    }}

    .sender-block {{
      flex: 1.2;
    }}

    .sender-name {{
      font-size: 20px;
      font-weight: 800;
      color: var(--primary);
      letter-spacing: -0.3px;
      text-transform: uppercase;
      margin-bottom: 4px;
    }}

    .sender-subtitle {{
      font-size: 13.5px;
      font-weight: 600;
      color: #374151;
      margin-bottom: 2px;
    }}

    .sender-school {{
      font-size: 13px;
      color: var(--text-muted);
      margin-bottom: 8px;
    }}

    .sender-contacts {{
      font-size: 12.5px;
      color: #4b5563;
      line-height: 1.5;
    }}

    .sender-contacts a {{
      color: var(--accent);
      text-decoration: none;
    }}

    .recipient-block {{
      flex: 1;
      background: #f9fafb;
      border-left: 3px solid var(--primary);
      padding: 14px 16px;
      border-radius: 0 8px 8px 0;
      font-size: 13px;
      line-height: 1.5;
    }}

    .date-line {{
      text-align: right;
      font-size: 13px;
      color: var(--text-muted);
      margin-bottom: 20px;
    }}

    /* Objet Box */
    .objet-box {{
      background: #eff6ff;
      border-left: 4px solid var(--primary);
      padding: 12px 18px;
      border-radius: 0 6px 6px 0;
      margin-bottom: 24px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }}

    .objet-text {{
      font-size: 14px;
      font-weight: 700;
      color: var(--primary);
    }}

    .badge {{
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.4px;
      padding: 4px 10px;
      border-radius: 9999px;
      background: #dbeafe;
      color: var(--primary);
    }}

    .badge-accent {{
      background: #dcfce7;
      color: #166534;
      border: 1px solid #bbf7d0;
    }}

    /* Letter Body */
    .letter-body {{
      font-size: 13.8px;
      color: #1f2937;
      text-align: justify;
      line-height: 1.65;
    }}

    .letter-body p {{
      margin-bottom: 14px;
    }}

    .letter-body strong {{
      color: #0f172a;
    }}

    .project-list {{
      list-style-type: none;
      padding-left: 0;
      margin: 12px 0 16px 0;
    }}

    .project-list li {{
      position: relative;
      padding-left: 20px;
      margin-bottom: 10px;
      font-size: 13.5px;
    }}

    .project-list li::before {{
      content: "▪";
      position: absolute;
      left: 4px;
      color: var(--primary);
      font-size: 14px;
    }}

    /* Sign block */
    .sign-block {{
      margin-top: 32px;
      display: flex;
      justify-content: flex-end;
    }}

    .signature-card {{
      text-align: right;
      min-width: 260px;
    }}

    .sign-name {{
      font-size: 16px;
      font-weight: 800;
      color: var(--primary);
    }}

    .sign-role {{
      font-size: 12.5px;
      color: var(--text-muted);
    }}

    /* Print styles */
    @media print {{
      body {{
        background: #ffffff !important;
        padding: 0 !important;
      }}

      .no-print {{
        display: none !important;
      }}

      .a4-container {{
        box-shadow: none !important;
        border: none !important;
        border-radius: 0 !important;
        max-width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
      }}

      @page {{
        size: A4 portrait;
        margin: 16mm 18mm 16mm 18mm;
      }}
    }}
  </style>
</head>
<body>

  <!-- Floating / Top Action Toolbar (hidden on print) -->
  <div class="toolbar no-print">
    <div class="toolbar-info">
      📄 <strong>Lettre de Motivation PFE</strong> générée pour <strong>{html.escape(company)}</strong> ({html.escape(title)})
    </div>
    <div class="toolbar-actions">
      <button class="btn" onclick="window.print()">
        🖨️ Imprimer en PDF (1-Clic)
      </button>
      <button class="btn btn-secondary" onclick="copyLetterText()">
        📋 Copier le Texte
      </button>
    </div>
  </div>

  <!-- A4 Printable Document Container -->
  <div class="a4-container" id="letterContainer">
    <header class="letter-header">
      <div class="sender-block">
        <div class="sender-name">{html.escape(cand.full_name)}</div>
        <div class="sender-subtitle">Élève-Ingénieur en 5ème Année – {html.escape(cand.specialization)}</div>
        <div class="sender-school">{html.escape(cand.school)}</div>
        <div class="sender-contacts">
          📍 {html.escape(cand.location)}<br>
          📞 {html.escape(cand.phone)} &nbsp;|&nbsp; ✉️ <a href="mailto:{html.escape(cand.email)}">{html.escape(cand.email)}</a><br>
          🔗 <a href="{html.escape(cand.linkedin_url)}" target="_blank">LinkedIn</a> &nbsp;|&nbsp;
          💻 <a href="{html.escape(cand.github_url)}" target="_blank">GitHub</a> &nbsp;|&nbsp;
          🌐 <a href="{html.escape(cand.portfolio_url)}" target="_blank">Portfolio</a>
        </div>
      </div>
      <div class="recipient-block">
        {recipient_html}
      </div>
    </header>

    <div class="date-line">
      Casablanca, le {date_str}
    </div>

    <div class="objet-box">
      <div class="objet-text">
        Objet : Candidature au {html.escape(objet_title)}
      </div>
      <div>
        <span class="badge">Stage PFE 4-6 mois</span>
        {pre_badge}
      </div>
    </div>

    <section class="letter-body">
      <p>Madame, Monsieur,</p>

      <p>
        Actuellement élève-ingénieur en 5ème année à l'<strong>{html.escape(cand.school)}</strong>,
        spécialisé en <strong>{html.escape(cand.specialization)}</strong>, je vous adresse avec un vif enthousiasme
        ma candidature pour l'opportunité de <strong>{html.escape(intro_role)}</strong> au sein de <strong>{html.escape(company)}</strong>.
      </p>


      <p>
        {company_p}
      </p>

      <p>
        Mon cursus d'ingénieur d'État et mes réalisations concrètes m'ont permis de développer une double compétence opérationnelle en <strong>Data Engineering</strong> et en <strong>Intelligence Artificielle</strong> :
      </p>

      <ul class="project-list">
        <li>
          <strong>Data Engineering & Streaming :</strong> Conception et déploiement d'une plateforme <em>Enterprise Media Lakehouse</em> (architecture Medallion Bronze/Silver/Gold) orchestrant plus de 100 000 flux de données quotidiens via des DAGs Apache Airflow, Apache Kafka et conteneurisation Docker multi-services.
        </li>
        <li>
          <strong>IA Avancée & Systèmes Intelligents :</strong> Conception d'un framework d'agents autonomes (<em>AI Multi-Agent Orchestrator</em>), intégration de pipelines RAG (Retrieval-Augmented Generation) avec recherche vectorielle sémantique et moteurs hybrides de graphes de connaissances (Neo4j / LLM).
        </li>
      </ul>

      <p>
        Cette assise technique est consolidée par des expériences industrielles probantes et mesurables :
      </p>

      <ul class="project-list">
        <li>
          <strong>Chez COSUMAR (Stage Ingénieur Data) :</strong> Conception et automatisation de pipelines ETL en Python et SQL pour plus de 20 KPIs opérationnels, réduisant le temps de génération des rapports d'activité de <strong>75%</strong> et le temps de diagnostic des anomalies opérationnelles de <strong>30%</strong>.
        </li>
        <li>
          <strong>Chez SEWS-CABINET (Sumitomo Electric Group) :</strong> Développement et déploiement d'applications industrielles collaboratives avec modules temps réel et architectures offline-first résilientes.
        </li>
      </ul>

      <p>
        {commitment_p}
      </p>

      <p>
        Disponible dès le <strong>début de l'année 2026 pour une période de 4 à 6 mois</strong>, je serais honoré d'échanger avec vous lors d'un entretien afin de vous exposer de vive voix la pertinence de mon profil et mon profond engagement à contribuer à la réussite de <strong>{html.escape(company)}</strong>.
      </p>

      <p>
        Vous remerciant par avance de l'attention bienveillante que vous porterez à ma candidature, je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations les plus distinguées.
      </p>

      <div class="sign-block">
        <div class="signature-card">
          <div class="sign-name">{html.escape(cand.full_name)}</div>
          <div class="sign-role">Élève-Ingénieur en 5ème Année – {html.escape(cand.specialization)}</div>
          <div class="sign-role">{html.escape(cand.school)}</div>
        </div>
      </div>
    </section>
  </div>

  <script>
    function copyLetterText() {{
      const text = `{raw_text_for_copy}`;
      navigator.clipboard.writeText(text).then(() => {{
        alert("✅ Texte de la lettre de motivation copié dans le presse-papier ! Vous pouvez le coller directement sur votre formulaire ou email.");
      }}).catch(() => {{
        alert("Veuillez sélectionner et copier le texte manuellement.");
      }});
    }}
  </script>
</body>
</html>"""

    @classmethod
    def save_letter_for_offer(
        cls,
        offer: JobOffer,
        output_dir: Optional[Path] = None,
        custom_slug: Optional[str] = None
    ) -> dict[str, Path]:
        """
        Generates and saves both .html (A4 print-ready) and .txt (plain text)
        versions of the formal cover letter for an offer.
        Returns a dict: {'html': html_path, 'txt': txt_path}.
        """
        out_dir = output_dir or (config.BASE_DIR / "letters")
        os.makedirs(out_dir, exist_ok=True)

        if custom_slug:
            slug = custom_slug
        else:
            safe_co = re.sub(r'[^a-zA-Z0-9]+', '_', offer.company or 'Entreprise').strip('_')
            safe_ti = re.sub(r'[^a-zA-Z0-9]+', '_', offer.title or 'PFE').strip('_')
            slug = f"Lettre_Motivation_{safe_co}_{safe_ti[:32]}_{offer.id[:6]}"

        html_path = out_dir / f"{slug}.html"
        txt_path = out_dir / f"{slug}.txt"

        html_content = cls.generate_formal_letter_html(offer)
        txt_content = cls.generate_formal_letter_text(offer)

        html_path.write_text(html_content, encoding="utf-8")
        txt_path.write_text(txt_content, encoding="utf-8")

        logger.info("Saved cover letter files for %s: %s, %s", offer.company, html_path.name, txt_path.name)
        return {"html": html_path, "txt": txt_path}

