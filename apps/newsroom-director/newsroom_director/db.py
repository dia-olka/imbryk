"""Database access layer for the Newsroom Director.

Connects to the same database as ingestion-api. Uses lightweight dataclasses
for decoupling from ingestion-api's SQLAlchemy models.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


# --- ORM models (mirrors of ingestion-api models) ---


class PromptRow(Base):
    __tablename__ = "prompts"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    text = Column(Text, nullable=False)
    payment_ref = Column(String(255), nullable=True)
    status = Column(String(32), nullable=False, default="accepted")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class CategorisedPromptRow(Base):
    __tablename__ = "categorised_prompts"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    prompt_id = Column(
        String(36), ForeignKey("prompts.id"), nullable=False
    )
    category_id = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class PaymentRefRow(Base):
    __tablename__ = "payment_refs"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    provider_transaction_id = Column(
        String(255), nullable=False, unique=True
    )
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(String(32), nullable=False, default="settled")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class WorldLedgerRow(Base):
    __tablename__ = "world_ledger"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    ledger_json = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow)


class EditionRow(Base):
    __tablename__ = "editions"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    date = Column(String(10), nullable=False)
    status = Column(String(32), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class EditionArticleRow(Base):
    __tablename__ = "edition_articles"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    edition_id = Column(
        String(36), ForeignKey("editions.id"), nullable=False
    )
    newspaper_id = Column(String(64), nullable=False)
    content_json = Column(Text, nullable=False)
    image_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class EditorialJournalRow(Base):
    __tablename__ = "editorial_journal"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    persona_id = Column(String(64), nullable=False)
    entry_date = Column(String(10), nullable=False)
    entry_type = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class EditionMetricRow(Base):
    __tablename__ = "edition_metrics"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    edition_date = Column(String(10), nullable=False)
    newspaper_id = Column(String(64), nullable=False)
    article_slug = Column(String(255), nullable=False)
    headline = Column(Text, nullable=False)
    page_views = Column(Integer, nullable=False, default=0)
    fetched_at = Column(DateTime(timezone=True), default=_utcnow)


class NewsItemRow(Base):
    __tablename__ = "news_items"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    edition_date = Column(String(10), nullable=False)
    category_id = Column(String(64), nullable=False)
    query = Column(Text, nullable=False)
    headline = Column(Text, nullable=False)
    snippet = Column(Text, nullable=False)
    source_url = Column(Text, nullable=False)
    relevance_score = Column(Float, nullable=False)
    status = Column(String(32), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class MarketingPostRow(Base):
    __tablename__ = "marketing_posts"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    edition_date = Column(String(10), nullable=False)
    channel = Column(String(32), nullable=False)
    post_type = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    post_url = Column(Text, nullable=True)
    post_id = Column(String(255), nullable=True)
    status = Column(String(32), nullable=False, default="posted")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


# --- Data transfer objects ---


@dataclass
class PromptRecord:
    prompt_id: str
    text: str
    payment_amount: float
    category_ids: list[str]


@dataclass
class NewsItemRecord:
    """A real-world news item fetched by the News Scout."""

    id: str
    edition_date: str
    category_id: str
    headline: str
    snippet: str
    source_url: str
    relevance_score: float


@dataclass
class JournalEntry:
    """A single editorial journal entry."""

    persona_id: str
    entry_date: str
    entry_type: str  # 'reflection', 'intention', 'observation'
    content: str


@dataclass
class ArticleMetric:
    """Page view data for a single article."""

    newspaper_id: str
    article_slug: str
    headline: str
    page_views: int


@dataclass
class MarketingPost:
    """A social media post created by the marketing agent."""

    edition_date: str
    channel: str
    post_type: str
    content: str
    post_url: str | None = None
    post_id: str | None = None
    status: str = "posted"


@dataclass
class EditionBackfillTarget:
    """An edition that has at least one newspaper with missing article images."""

    edition_id: str
    edition_date: str
    # All newspaper articles for this edition (newspaper_id -> content_json).
    # Includes curator. Required so write_edition can re-upload the full envelope.
    newspaper_articles: dict[str, str]
    # Subset of newspaper_ids that have articles with imagePrompt but no image_url.
    newspapers_to_backfill: list[str]


# --- Engine / session helpers ---


def get_engine(database_url: str):
    return create_engine(database_url, echo=False)


def get_session_factory(engine):
    return sessionmaker(bind=engine)


# --- Query functions ---


def fetch_unprocessed_prompts(session: Session) -> list[PromptRecord]:
    """Fetch prompts with status='accepted', joining categories and payments."""
    rows = (
        session.query(
            PromptRow.id,
            PromptRow.text,
            PromptRow.payment_ref,
        )
        .filter(PromptRow.status == "accepted")
        .all()
    )

    results: list[PromptRecord] = []
    for row in rows:
        prompt_id, text, payment_ref = row

        # Get categories
        cat_rows = (
            session.query(CategorisedPromptRow.category_id)
            .filter(CategorisedPromptRow.prompt_id == prompt_id)
            .all()
        )
        category_ids = [c[0] for c in cat_rows]

        # Get payment amount
        payment_amount = 0.0
        if payment_ref:
            pay_row = (
                session.query(PaymentRefRow.amount)
                .filter(
                    PaymentRefRow.provider_transaction_id == payment_ref
                )
                .first()
            )
            if pay_row:
                payment_amount = pay_row[0]

        results.append(
            PromptRecord(
                prompt_id=prompt_id,
                text=text,
                payment_amount=payment_amount,
                category_ids=category_ids,
            )
        )

    return results


def mark_prompts_processed(
    session: Session, prompt_ids: list[str]
) -> None:
    """Set status='processed' for the given prompt IDs."""
    if not prompt_ids:
        return
    session.query(PromptRow).filter(PromptRow.id.in_(prompt_ids)).update(
        {"status": "processed"}, synchronize_session="fetch"
    )


def load_world_ledger(session: Session) -> dict | None:
    """Read the canonical WorldLedger JSON from the DB."""
    row = session.query(WorldLedgerRow).first()
    if row is None:
        return None
    return json.loads(row.ledger_json)


def save_world_ledger(session: Session, ledger_dict: dict) -> None:
    """Upsert the canonical WorldLedger JSON."""
    row = session.query(WorldLedgerRow).first()
    ledger_json = json.dumps(ledger_dict, ensure_ascii=False)

    if row is None:
        row = WorldLedgerRow(
            id=_new_uuid(),
            ledger_json=ledger_json,
            updated_at=_utcnow(),
        )
        session.add(row)
    else:
        row.ledger_json = ledger_json
        row.updated_at = _utcnow()


def save_edition(
    session: Session,
    edition_date: str,
    articles: dict[str, str],
) -> str:
    """Write an edition and its articles to the DB. Returns edition ID."""
    edition_id = _new_uuid()
    edition = EditionRow(
        id=edition_id,
        date=edition_date,
        status="published",
    )
    session.add(edition)
    session.flush()  # ensure edition row exists before inserting articles

    for newspaper_id, content in articles.items():
        article = EditionArticleRow(
            id=_new_uuid(),
            edition_id=edition_id,
            newspaper_id=newspaper_id,
            content_json=content,
        )
        session.add(article)

    return edition_id


def update_article_content_json(
    session: Session,
    edition_id: str,
    newspaper_id: str,
    content_json: str,
) -> None:
    """Overwrite content_json for a specific edition article row.

    Called by the image backfill step after successfully generating images so
    that subsequent runs do not re-query and re-generate the same images.
    """
    row = (
        session.query(EditionArticleRow)
        .filter(
            EditionArticleRow.edition_id == edition_id,
            EditionArticleRow.newspaper_id == newspaper_id,
        )
        .first()
    )
    if row is not None:
        row.content_json = content_json


def fetch_editions_needing_image_backfill(
    session: Session,
    exclude_date: str,
    max_editions: int = 7,
) -> list[EditionBackfillTarget]:
    """Return previous editions that have articles with imagePrompt but no image_url.

    Scans the last *max_editions* editions (by date, descending), excluding
    *exclude_date* (today). For each edition, parses every newspaper's
    content_json and identifies which newspapers have at least one article
    that needs an image.

    Args:
        session: Active DB session.
        exclude_date: Date string (YYYY-MM-DD) to exclude from the scan.
        max_editions: Maximum number of past editions to inspect.

    Returns:
        List of EditionBackfillTarget, one per edition that needs backfill.
    """
    edition_rows = (
        session.query(EditionRow)
        .filter(EditionRow.date != exclude_date)
        .order_by(EditionRow.date.desc())
        .limit(max_editions)
        .all()
    )

    targets: list[EditionBackfillTarget] = []

    for edition_row in edition_rows:
        article_rows = (
            session.query(EditionArticleRow)
            .filter(EditionArticleRow.edition_id == edition_row.id)
            .all()
        )

        newspaper_articles: dict[str, str] = {}
        newspapers_to_backfill: list[str] = []

        for article_row in article_rows:
            newspaper_articles[article_row.newspaper_id] = article_row.content_json

            if article_row.newspaper_id == "curator":
                continue

            try:
                parsed = json.loads(article_row.content_json)
            except (json.JSONDecodeError, TypeError):
                continue

            needs_backfill = any(
                isinstance(a, dict) and a.get("imagePrompt") and not a.get("image_url")
                for a in parsed.get("articles", [])
            )
            if needs_backfill:
                newspapers_to_backfill.append(article_row.newspaper_id)

        if newspapers_to_backfill:
            targets.append(
                EditionBackfillTarget(
                    edition_id=edition_row.id,
                    edition_date=edition_row.date,
                    newspaper_articles=newspaper_articles,
                    newspapers_to_backfill=newspapers_to_backfill,
                )
            )

    return targets


# --- News Scout queries ---


def save_news_item(
    session: Session,
    edition_date: str,
    category_id: str,
    query: str,
    headline: str,
    snippet: str,
    source_url: str,
    relevance_score: float,
) -> bool:
    """Insert a news item, returning True on success.

    Returns False if a row with the same (source_url, edition_date) already
    exists. Checks for duplicates before inserting to work with both SQLite
    (which may not enforce named unique constraints from migrations) and
    PostgreSQL.
    """
    existing = (
        session.query(NewsItemRow.id)
        .filter(
            NewsItemRow.source_url == source_url,
            NewsItemRow.edition_date == edition_date,
        )
        .first()
    )
    if existing is not None:
        return False

    row = NewsItemRow(
        id=_new_uuid(),
        edition_date=edition_date,
        category_id=category_id,
        query=query,
        headline=headline,
        snippet=snippet,
        source_url=source_url,
        relevance_score=relevance_score,
    )
    session.add(row)
    session.flush()
    return True


def fetch_pending_news_items(
    session: Session, edition_date: str
) -> list[NewsItemRecord]:
    """Fetch news items with status='pending' for the given edition date."""
    rows = (
        session.query(NewsItemRow)
        .filter(
            NewsItemRow.edition_date == edition_date,
            NewsItemRow.status == "pending",
        )
        .all()
    )
    return [
        NewsItemRecord(
            id=row.id,
            edition_date=row.edition_date,
            category_id=row.category_id,
            headline=row.headline,
            snippet=row.snippet,
            source_url=row.source_url,
            relevance_score=row.relevance_score,
        )
        for row in rows
    ]


def mark_news_items_processed(
    session: Session, edition_date: str
) -> None:
    """Set status='processed' for all news items of the given edition date."""
    session.query(NewsItemRow).filter(
        NewsItemRow.edition_date == edition_date,
        NewsItemRow.status == "pending",
    ).update({"status": "processed"}, synchronize_session="fetch")


# --- Editorial Journal queries ---


def save_journal_entry(
    session: Session,
    persona_id: str,
    entry_date: str,
    entry_type: str,
    content: str,
) -> None:
    """Upsert an editorial journal entry.

    If an entry for (persona_id, entry_date, entry_type) already exists,
    its content is replaced.
    """
    existing = (
        session.query(EditorialJournalRow)
        .filter(
            EditorialJournalRow.persona_id == persona_id,
            EditorialJournalRow.entry_date == entry_date,
            EditorialJournalRow.entry_type == entry_type,
        )
        .first()
    )
    if existing is not None:
        existing.content = content
        existing.created_at = _utcnow()
    else:
        row = EditorialJournalRow(
            id=_new_uuid(),
            persona_id=persona_id,
            entry_date=entry_date,
            entry_type=entry_type,
            content=content,
            created_at=_utcnow(),
        )
        session.add(row)


def load_recent_journal(
    session: Session,
    persona_id: str,
    lookback_days: int = 7,
    current_date: str = "",
) -> list[JournalEntry]:
    """Load recent editorial journal entries for a persona.

    Returns entries from the last *lookback_days* days, ordered by date
    ascending (oldest first). Also includes pipeline-level observations
    (persona_id='_pipeline') from the same window.

    Args:
        session: Active DB session.
        persona_id: The persona to load entries for.
        lookback_days: How many days back to look.
        current_date: The current edition date (YYYY-MM-DD). Used to
            compute the lookback window.

    Returns:
        List of JournalEntry, ordered by date ascending.
    """
    if not current_date:
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Compute cutoff date
    cutoff_dt = datetime.strptime(current_date, "%Y-%m-%d") - timedelta(
        days=lookback_days
    )
    cutoff_date = cutoff_dt.strftime("%Y-%m-%d")

    rows = (
        session.query(EditorialJournalRow)
        .filter(
            EditorialJournalRow.persona_id.in_([persona_id, "_pipeline"]),
            EditorialJournalRow.entry_date > cutoff_date,
            EditorialJournalRow.entry_date < current_date,
        )
        .order_by(EditorialJournalRow.entry_date.asc())
        .all()
    )

    return [
        JournalEntry(
            persona_id=row.persona_id,
            entry_date=row.entry_date,
            entry_type=row.entry_type,
            content=row.content,
        )
        for row in rows
    ]


# --- Edition Metrics queries ---


def save_edition_metrics(
    session: Session,
    metrics: list[ArticleMetric],
    edition_date: str,
) -> int:
    """Upsert article page-view metrics for an edition.

    Returns the number of rows written.
    """
    written = 0
    for m in metrics:
        existing = (
            session.query(EditionMetricRow)
            .filter(
                EditionMetricRow.edition_date == edition_date,
                EditionMetricRow.newspaper_id == m.newspaper_id,
                EditionMetricRow.article_slug == m.article_slug,
            )
            .first()
        )
        if existing is not None:
            existing.page_views = m.page_views
            existing.headline = m.headline
            existing.fetched_at = _utcnow()
        else:
            row = EditionMetricRow(
                id=_new_uuid(),
                edition_date=edition_date,
                newspaper_id=m.newspaper_id,
                article_slug=m.article_slug,
                headline=m.headline,
                page_views=m.page_views,
                fetched_at=_utcnow(),
            )
            session.add(row)
        written += 1
    return written


def load_edition_metrics(
    session: Session,
    edition_date: str,
) -> dict[str, list[ArticleMetric]]:
    """Load page-view metrics for a given edition date.

    Returns a dict keyed by newspaper_id, each containing a list of
    ArticleMetric sorted by page_views descending.
    """
    rows = (
        session.query(EditionMetricRow)
        .filter(EditionMetricRow.edition_date == edition_date)
        .order_by(
            EditionMetricRow.newspaper_id,
            EditionMetricRow.page_views.desc(),
        )
        .all()
    )

    result: dict[str, list[ArticleMetric]] = {}
    for row in rows:
        metric = ArticleMetric(
            newspaper_id=row.newspaper_id,
            article_slug=row.article_slug,
            headline=row.headline,
            page_views=row.page_views,
        )
        result.setdefault(row.newspaper_id, []).append(metric)

    return result


# --- Marketing posts ---


def save_marketing_post(
    session: Session,
    post: MarketingPost,
) -> None:
    """Save a marketing post record."""
    row = MarketingPostRow(
        id=_new_uuid(),
        edition_date=post.edition_date,
        channel=post.channel,
        post_type=post.post_type,
        content=post.content,
        post_url=post.post_url,
        post_id=post.post_id,
        status=post.status,
        created_at=_utcnow(),
    )
    session.add(row)


def load_recent_marketing_posts(
    session: Session,
    lookback_days: int = 7,
    current_date: str = "",
) -> list[MarketingPost]:
    """Load marketing posts from the last N days."""
    if not current_date:
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    cutoff_dt = datetime.strptime(current_date, "%Y-%m-%d") - timedelta(
        days=lookback_days
    )
    cutoff_date = cutoff_dt.strftime("%Y-%m-%d")

    rows = (
        session.query(MarketingPostRow)
        .filter(
            MarketingPostRow.edition_date > cutoff_date,
            MarketingPostRow.edition_date <= current_date,
        )
        .order_by(MarketingPostRow.created_at.desc())
        .all()
    )

    return [
        MarketingPost(
            edition_date=row.edition_date,
            channel=row.channel,
            post_type=row.post_type,
            content=row.content,
            post_url=row.post_url,
            post_id=row.post_id,
            status=row.status,
        )
        for row in rows
    ]


# --- Edition loading (used by marketing agent) ---


def load_edition_by_date(
    session: Session,
    edition_date: str,
) -> dict[str, str] | None:
    """Load edition articles for a given date.

    Returns dict of {newspaper_id: content_json} or None if not found.
    """
    edition_row = (
        session.query(EditionRow)
        .filter(EditionRow.date == edition_date)
        .first()
    )
    if edition_row is None:
        return None

    article_rows = (
        session.query(EditionArticleRow)
        .filter(EditionArticleRow.edition_id == edition_row.id)
        .all()
    )

    return {row.newspaper_id: row.content_json for row in article_rows}
